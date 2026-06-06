import argparse
import csv
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from flask import Flask, jsonify, request


BASE_DIR = Path(__file__).resolve().parent.parent
COORDINATOR_DIR = BASE_DIR / "coordinator"
LOG_FILE = COORDINATOR_DIR / "coordinator_log.csv"

NODE_URLS = {
    "A": "http://127.0.0.1:5001",
    "B": "http://127.0.0.1:5002",
    "C": "http://127.0.0.1:5003",
}

app = Flask(__name__)


def ensure_log_file():
    if LOG_FILE.exists():
        return

    with open(LOG_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "transaction_id",
                "latency_ms",
                "decision",
                "status",
                "prepare_phase_ms",
                "decision_phase_ms",
                "total_time_ms",
                "doing_work_ms",
                "network_wait_ms",
                "coordination_cost_percent",
                "failed_nodes",
                "prepare_results",
                "decision_results",
                "created_at",
            ],
        )
        writer.writeheader()


def append_log(row: dict):
    ensure_log_file()

    with open(LOG_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "transaction_id",
                "latency_ms",
                "decision",
                "status",
                "prepare_phase_ms",
                "decision_phase_ms",
                "total_time_ms",
                "doing_work_ms",
                "network_wait_ms",
                "coordination_cost_percent",
                "failed_nodes",
                "prepare_results",
                "decision_results",
                "created_at",
            ],
        )
        writer.writerow(row)


def post_to_node(node_id: str, endpoint: str, payload: dict, timeout_seconds: float):
    url = f"{NODE_URLS[node_id]}{endpoint}"
    start = time.perf_counter()

    try:
        response = requests.post(url, json=payload, timeout=timeout_seconds)
        elapsed_ms = (time.perf_counter() - start) * 1000

        try:
            data = response.json()
        except Exception:
            data = {
                "raw_response": response.text
            }

        return {
            "node": node_id,
            "ok": response.ok,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
            "data": data,
            "error": None,
        }

    except requests.exceptions.Timeout:
        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "node": node_id,
            "ok": False,
            "status_code": None,
            "elapsed_ms": elapsed_ms,
            "data": None,
            "error": "TIMEOUT",
        }

    except requests.exceptions.ConnectionError:
        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "node": node_id,
            "ok": False,
            "status_code": None,
            "elapsed_ms": elapsed_ms,
            "data": None,
            "error": "CONNECTION_ERROR",
        }

    except Exception as exception:
        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "node": node_id,
            "ok": False,
            "status_code": None,
            "elapsed_ms": elapsed_ms,
            "data": None,
            "error": str(exception),
        }


def send_parallel(endpoint: str, payload: dict, timeout_seconds: float):
    results = []

    with ThreadPoolExecutor(max_workers=len(NODE_URLS)) as executor:
        future_map = {
            executor.submit(post_to_node, node_id, endpoint, payload, timeout_seconds): node_id
            for node_id in NODE_URLS
        }

        for future in as_completed(future_map):
            results.append(future.result())

    results.sort(key=lambda item: item["node"])
    return results


def get_vote(result: dict):
    data = result.get("data") or {}
    return data.get("vote")


def get_ack(result: dict):
    data = result.get("data") or {}
    return data.get("ack")


def get_work_time_ms(result: dict):
    data = result.get("data") or {}

    try:
        return float(data.get("work_time_ms", 0))
    except Exception:
        return 0.0


def calculate_max_work_time(results: list):
    if not results:
        return 0.0

    return max(get_work_time_ms(result) for result in results)


def extract_failed_nodes(prepare_results: list):
    failed_nodes = []

    for result in prepare_results:
        vote = get_vote(result)

        if not result["ok"] or vote != "YES":
            failed_nodes.append({
                "node": result["node"],
                "status_code": result["status_code"],
                "vote": vote,
                "error": result["error"],
                "data": result["data"],
            })

    return failed_nodes


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "coordinator": "UP",
        "nodes": NODE_URLS,
    })


@app.route("/transaction", methods=["POST"])
def run_transaction():
    data = request.get_json() or {}

    transaction_id = data.get("transaction_id") or data.get("tx_id")
    from_account = data.get("from_account")
    to_account = data.get("to_account")
    amount = data.get("amount")
    latency_ms = float(data.get("latency_ms", 0))

    timeout_seconds = float(data.get("timeout_seconds", 5))

    if not transaction_id or not from_account or not to_account or amount is None:
        return jsonify({
            "status": "FAILED",
            "message": "Missing required fields: transaction_id, from_account, to_account, amount"
        }), 400

    payload = {
        "transaction_id": transaction_id,
        "from_account": from_account,
        "to_account": to_account,
        "amount": amount,
        "latency_ms": latency_ms,
    }

    total_start = time.perf_counter()

    # Phase 1: PREPARE / VOTING
    prepare_start = time.perf_counter()
    prepare_results = send_parallel("/prepare", payload, timeout_seconds)
    prepare_phase_ms = (time.perf_counter() - prepare_start) * 1000

    failed_nodes = extract_failed_nodes(prepare_results)

    if len(failed_nodes) == 0:
        decision = "COMMIT"
        decision_endpoint = "/commit"
    else:
        decision = "ABORT"
        decision_endpoint = "/abort"

    decision_payload = {
        "transaction_id": transaction_id,
        "latency_ms": latency_ms,
    }

    # Phase 2: COMMIT / ABORT
    decision_start = time.perf_counter()
    decision_results = send_parallel(decision_endpoint, decision_payload, timeout_seconds)
    decision_phase_ms = (time.perf_counter() - decision_start) * 1000

    total_time_ms = (time.perf_counter() - total_start) * 1000

    prepare_work_ms = calculate_max_work_time(prepare_results)
    decision_work_ms = calculate_max_work_time(decision_results)
    doing_work_ms = prepare_work_ms + decision_work_ms

    network_wait_ms = max(total_time_ms - doing_work_ms, 0)

    if total_time_ms > 0:
        coordination_cost_percent = (network_wait_ms / total_time_ms) * 100
    else:
        coordination_cost_percent = 0

    if decision == "COMMIT":
        status = "SUCCESS"
    else:
        status = "FAILED"

    result = {
        "transaction_id": transaction_id,
        "latency_ms": latency_ms,
        "decision": decision,
        "status": status,
        "prepare_phase_ms": prepare_phase_ms,
        "decision_phase_ms": decision_phase_ms,
        "total_time_ms": total_time_ms,
        "doing_work_ms": doing_work_ms,
        "network_wait_ms": network_wait_ms,
        "coordination_cost_percent": coordination_cost_percent,
        "failed_nodes": failed_nodes,
        "prepare_results": prepare_results,
        "decision_results": decision_results,
    }

    append_log({
        "transaction_id": transaction_id,
        "latency_ms": latency_ms,
        "decision": decision,
        "status": status,
        "prepare_phase_ms": prepare_phase_ms,
        "decision_phase_ms": decision_phase_ms,
        "total_time_ms": total_time_ms,
        "doing_work_ms": doing_work_ms,
        "network_wait_ms": network_wait_ms,
        "coordination_cost_percent": coordination_cost_percent,
        "failed_nodes": json.dumps(failed_nodes, ensure_ascii=False),
        "prepare_results": json.dumps(prepare_results, ensure_ascii=False),
        "decision_results": json.dumps(decision_results, ensure_ascii=False),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    })

    return jsonify(result)


@app.route("/logs", methods=["GET"])
def logs():
    ensure_log_file()

    limit = int(request.args.get("limit", 20))

    rows = []

    with open(LOG_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            rows.append(row)

    rows = rows[-limit:]

    return jsonify({
        "log_file": str(LOG_FILE),
        "logs": rows,
    })


@app.route("/nodes/health", methods=["GET"])
def nodes_health():
    results = []

    for node_id, base_url in NODE_URLS.items():
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            results.append({
                "node": node_id,
                "ok": response.ok,
                "status_code": response.status_code,
                "data": response.json(),
            })
        except Exception as exception:
            results.append({
                "node": node_id,
                "ok": False,
                "status_code": None,
                "error": str(exception),
            })

    return jsonify({
        "nodes": results
    })


def parse_arguments():
    parser = argparse.ArgumentParser(description="Coordinator Server")
    parser.add_argument("--port", required=False, type=int, default=8000)
    return parser.parse_args()


def main():
    args = parse_arguments()
    ensure_log_file()

    print("Starting Coordinator")
    print(f"Port: {args.port}")
    print(f"Log file: {LOG_FILE}")

    app.run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()