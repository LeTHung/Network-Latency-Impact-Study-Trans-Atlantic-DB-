import argparse
import time
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "financial_transactions.csv"
RAW_FILE = BASE_DIR / "benchmark" / "results_raw.csv"
SUMMARY_FILE = BASE_DIR / "benchmark" / "results_summary.csv"


def parse_args():
    parser = argparse.ArgumentParser(description="Run benchmark for Trans-Atlantic DB")

    parser.add_argument("--latency", type=float, required=True, help="Latency in ms: 1, 50, 250")
    parser.add_argument("--runs", type=int, default=5, help="Number of benchmark runs")
    parser.add_argument("--transactions", type=int, default=100, help="Transactions per run")
    parser.add_argument("--warmup", type=int, default=20, help="Warm-up transactions")
    parser.add_argument("--coordinator-url", default="http://127.0.0.1:8000")
    parser.add_argument("--fixed-amount", type=float, default=10.0)
    parser.add_argument("--reset", action="store_true", help="Delete old benchmark results before running")

    return parser.parse_args()


def load_transactions():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Không tìm thấy dataset: {DATA_FILE}")

    df = pd.read_csv(DATA_FILE)

    required_cols = ["transaction_id", "from_account", "to_account", "amount"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Dataset thiếu cột: {col}")

    return df


def call_transaction(coordinator_url, row, latency_ms, run_id, tx_index, fixed_amount):
    tx_id = f"BM_L{int(latency_ms)}_R{run_id}_T{tx_index}_{uuid.uuid4().hex[:8]}"

    payload = {
        "transaction_id": tx_id,
        "from_account": row["from_account"],
        "to_account": row["to_account"],
        "amount": fixed_amount,
        "latency_ms": latency_ms,
    }

    start = time.perf_counter()

    try:
        response = requests.post(
            f"{coordinator_url}/transaction",
            json=payload,
            timeout=max(10, latency_ms / 1000 * 10 + 10),
        )

        client_elapsed_ms = (time.perf_counter() - start) * 1000

        try:
            data = response.json()
        except Exception:
            data = {}

        return {
            "benchmark_run": run_id,
            "transaction_index": tx_index,
            "latency_ms": latency_ms,
            "transaction_id": tx_id,
            "from_account": payload["from_account"],
            "to_account": payload["to_account"],
            "amount": fixed_amount,
            "http_status": response.status_code,
            "client_elapsed_ms": client_elapsed_ms,
            "decision": data.get("decision", "UNKNOWN"),
            "status": data.get("status", "UNKNOWN"),
            "prepare_phase_ms": data.get("prepare_phase_ms", np.nan),
            "decision_phase_ms": data.get("decision_phase_ms", np.nan),
            "total_time_ms": data.get("total_time_ms", np.nan),
            "doing_work_ms": data.get("doing_work_ms", np.nan),
            "network_wait_ms": data.get("network_wait_ms", np.nan),
            "coordination_cost_percent": data.get("coordination_cost_percent", np.nan),
            "failed_nodes": str(data.get("failed_nodes", [])),
            "error": "",
        }

    except Exception as e:
        client_elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "benchmark_run": run_id,
            "transaction_index": tx_index,
            "latency_ms": latency_ms,
            "transaction_id": tx_id,
            "from_account": payload["from_account"],
            "to_account": payload["to_account"],
            "amount": fixed_amount,
            "http_status": None,
            "client_elapsed_ms": client_elapsed_ms,
            "decision": "ERROR",
            "status": "FAILED",
            "prepare_phase_ms": np.nan,
            "decision_phase_ms": np.nan,
            "total_time_ms": np.nan,
            "doing_work_ms": np.nan,
            "network_wait_ms": np.nan,
            "coordination_cost_percent": np.nan,
            "failed_nodes": "",
            "error": str(e),
        }


def append_raw_results(records):
    df_new = pd.DataFrame(records)

    if RAW_FILE.exists() and RAW_FILE.stat().st_size > 0:
        df_old = pd.read_csv(RAW_FILE)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all.to_csv(RAW_FILE, index=False, encoding="utf-8-sig")
    return df_all


def build_summary(df):
    valid = df.dropna(subset=["total_time_ms"]).copy()

    if valid.empty:
        raise ValueError("Không có dữ liệu benchmark hợp lệ để tính summary.")

    summary_rows = []

    for latency, group in valid.groupby("latency_ms"):
        total = len(group)
        success = (group["status"] == "SUCCESS").sum()
        failed = total - success

        summary_rows.append({
            "latency_ms": latency,
            "transactions": total,
            "success_count": success,
            "failed_count": failed,
            "abort_rate_percent": failed / total * 100,
            "mean_total_time_ms": group["total_time_ms"].mean(),
            "median_total_time_ms": group["total_time_ms"].median(),
            "p99_total_time_ms": group["total_time_ms"].quantile(0.99),
            "min_total_time_ms": group["total_time_ms"].min(),
            "max_total_time_ms": group["total_time_ms"].max(),
            "std_total_time_ms": group["total_time_ms"].std(),
            "mean_prepare_phase_ms": group["prepare_phase_ms"].mean(),
            "mean_decision_phase_ms": group["decision_phase_ms"].mean(),
            "mean_doing_work_ms": group["doing_work_ms"].mean(),
            "mean_network_wait_ms": group["network_wait_ms"].mean(),
            "mean_coordination_cost_percent": group["coordination_cost_percent"].mean(),
        })

    summary = pd.DataFrame(summary_rows).sort_values("latency_ms")
    summary.to_csv(SUMMARY_FILE, index=False, encoding="utf-8-sig")

    return summary


def main():
    args = parse_args()

    if args.reset:
        for file in [RAW_FILE, SUMMARY_FILE]:
            if file.exists():
                file.unlink()

    df = load_transactions()

    total_needed = args.warmup + args.runs * args.transactions

    if total_needed > len(df):
        df = df.sample(total_needed, replace=True, random_state=42).reset_index(drop=True)
    else:
        df = df.sample(total_needed, random_state=42).reset_index(drop=True)

    print(f"Benchmark latency = {args.latency} ms")
    print(f"Warm-up = {args.warmup}")
    print(f"Runs = {args.runs}")
    print(f"Transactions per run = {args.transactions}")
    print(f"Coordinator = {args.coordinator_url}")

    cursor = 0

    print("\nRunning warm-up...")
    for i in range(args.warmup):
        row = df.iloc[cursor]
        cursor += 1
        call_transaction(
            args.coordinator_url,
            row,
            args.latency,
            run_id=0,
            tx_index=i + 1,
            fixed_amount=args.fixed_amount,
        )

    print("Warm-up completed.")

    records = []

    for run_id in range(1, args.runs + 1):
        print(f"\nRun {run_id}/{args.runs}")

        for tx_index in range(1, args.transactions + 1):
            row = df.iloc[cursor]
            cursor += 1

            record = call_transaction(
                args.coordinator_url,
                row,
                args.latency,
                run_id=run_id,
                tx_index=tx_index,
                fixed_amount=args.fixed_amount,
            )

            records.append(record)

            if tx_index % 10 == 0:
                print(f"  Completed {tx_index}/{args.transactions}")

    df_all = append_raw_results(records)
    summary = build_summary(df_all)

    print("\nBenchmark finished.")
    print(f"Raw results: {RAW_FILE}")
    print(f"Summary: {SUMMARY_FILE}")
    print("\nCurrent summary:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()