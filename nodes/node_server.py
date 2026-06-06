import argparse
import sqlite3
import time
from pathlib import Path
from flask import Flask, jsonify, request


BASE_DIR = Path(__file__).resolve().parent.parent
NODES_DIR = BASE_DIR / "nodes"

NODE_DATABASES = {
    "A": NODES_DIR / "node_a.db",
    "B": NODES_DIR / "node_b.db",
    "C": NODES_DIR / "node_c.db",
}

app = Flask(__name__)

NODE_ID = None
DB_PATH = None
NODE_ACTIVE = True


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def simulate_latency(latency_ms: float):
    if latency_ms > 0:
        time.sleep(latency_ms / 1000)


def log_event(tx_id: str, phase: str, decision: str, message: str):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO transaction_log (tx_id, phase, decision, message)
            VALUES (?, ?, ?, ?)
            """,
            (tx_id, phase, decision, message)
        )
        connection.commit()


def get_account(connection, account_id: str):
    cursor = connection.cursor()
    cursor.execute(
        "SELECT account_id, balance, node FROM accounts WHERE account_id = ?",
        (account_id,)
    )
    return cursor.fetchone()


def determine_role(connection, from_account: str, to_account: str):
    from_row = get_account(connection, from_account)
    to_row = get_account(connection, to_account)

    has_from = from_row is not None
    has_to = to_row is not None

    if has_from and has_to:
        return "DEBIT_CREDIT", from_row, to_row

    if has_from:
        return "DEBIT", from_row, None

    if has_to:
        return "CREDIT", None, to_row

    return "NONE", None, None


@app.route("/health", methods=["GET"])
def health():
    if not NODE_ACTIVE:
        return jsonify({
            "node": NODE_ID,
            "status": "DOWN"
        }), 503

    return jsonify({
        "node": NODE_ID,
        "status": "UP"
    })


@app.route("/prepare", methods=["POST"])
def prepare():
    global NODE_ACTIVE

    if not NODE_ACTIVE:
        return jsonify({
            "node": NODE_ID,
            "vote": "NO",
            "reason": "Node is down"
        }), 503

    data = request.get_json() or {}

    tx_id = data.get("transaction_id") or data.get("tx_id")
    from_account = data.get("from_account")
    to_account = data.get("to_account")
    amount = float(data.get("amount", 0))
    latency_ms = float(data.get("latency_ms", 0))

    simulate_latency(latency_ms)

    work_start = time.perf_counter()

    try:
        with get_connection() as connection:
            role, from_row, to_row = determine_role(connection, from_account, to_account)

            if role == "NONE":
                log_event(
                    tx_id,
                    "PREPARE",
                    "YES",
                    f"Node {NODE_ID} is not involved in this Transaction."
                )

                work_time_ms = (time.perf_counter() - work_start) * 1000
                simulate_latency(latency_ms)

                return jsonify({
                    "node": NODE_ID,
                    "vote": "YES",
                    "role": role,
                    "work_time_ms": work_time_ms,
                    "message": "Node is not involved."
                })

            if role in ("DEBIT", "DEBIT_CREDIT"):
                if from_row["balance"] < amount:
                    log_event(
                        tx_id,
                        "PREPARE",
                        "NO",
                        f"Insufficient balance. Current balance = {from_row['balance']}, amount = {amount}"
                    )

                    work_time_ms = (time.perf_counter() - work_start) * 1000
                    simulate_latency(latency_ms)

                    return jsonify({
                        "node": NODE_ID,
                        "vote": "NO",
                        "role": role,
                        "work_time_ms": work_time_ms,
                        "reason": "Insufficient balance"
                    })

            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO pending_transactions
                (tx_id, from_account, to_account, amount, role, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (tx_id, from_account, to_account, amount, role, "PREPARED")
            )
            connection.commit()

            log_event(
                tx_id,
                "PREPARE",
                "YES",
                f"Node {NODE_ID} voted YES with role {role}."
            )

            work_time_ms = (time.perf_counter() - work_start) * 1000
            simulate_latency(latency_ms)

            return jsonify({
                "node": NODE_ID,
                "vote": "YES",
                "role": role,
                "work_time_ms": work_time_ms,
                "message": "Prepared successfully"
            })

    except Exception as exception:
        work_time_ms = (time.perf_counter() - work_start) * 1000
        simulate_latency(latency_ms)

        try:
            log_event(tx_id, "PREPARE", "NO", str(exception))
        except Exception:
            pass

        return jsonify({
            "node": NODE_ID,
            "vote": "NO",
            "work_time_ms": work_time_ms,
            "reason": str(exception)
        }), 500


@app.route("/commit", methods=["POST"])
def commit():
    global NODE_ACTIVE

    if not NODE_ACTIVE:
        return jsonify({
            "node": NODE_ID,
            "ack": False,
            "reason": "Node is down"
        }), 503

    data = request.get_json() or {}

    tx_id = data.get("transaction_id") or data.get("tx_id")
    latency_ms = float(data.get("latency_ms", 0))

    simulate_latency(latency_ms)

    work_start = time.perf_counter()

    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT tx_id, from_account, to_account, amount, role, status
                FROM pending_transactions
                WHERE tx_id = ?
                """,
                (tx_id,)
            )
            pending = cursor.fetchone()

            if pending is None:
                log_event(
                    tx_id,
                    "COMMIT",
                    "ACK",
                    f"Node {NODE_ID} has no local change for this Transaction."
                )

                work_time_ms = (time.perf_counter() - work_start) * 1000
                simulate_latency(latency_ms)

                return jsonify({
                    "node": NODE_ID,
                    "ack": True,
                    "work_time_ms": work_time_ms,
                    "message": "No local change"
                })

            role = pending["role"]
            from_account = pending["from_account"]
            to_account = pending["to_account"]
            amount = float(pending["amount"])

            if role in ("DEBIT", "DEBIT_CREDIT"):
                cursor.execute(
                    """
                    UPDATE accounts
                    SET balance = balance - ?
                    WHERE account_id = ?
                    """,
                    (amount, from_account)
                )

            if role in ("CREDIT", "DEBIT_CREDIT"):
                cursor.execute(
                    """
                    UPDATE accounts
                    SET balance = balance + ?
                    WHERE account_id = ?
                    """,
                    (amount, to_account)
                )

            cursor.execute(
                """
                UPDATE pending_transactions
                SET status = ?
                WHERE tx_id = ?
                """,
                ("COMMITTED", tx_id)
            )

            connection.commit()

            log_event(
                tx_id,
                "COMMIT",
                "ACK",
                f"Node {NODE_ID} committed Transaction with role {role}."
            )

            work_time_ms = (time.perf_counter() - work_start) * 1000
            simulate_latency(latency_ms)

            return jsonify({
                "node": NODE_ID,
                "ack": True,
                "role": role,
                "work_time_ms": work_time_ms,
                "message": "Committed successfully"
            })

    except Exception as exception:
        work_time_ms = (time.perf_counter() - work_start) * 1000
        simulate_latency(latency_ms)

        try:
            log_event(tx_id, "COMMIT", "ERROR", str(exception))
        except Exception:
            pass

        return jsonify({
            "node": NODE_ID,
            "ack": False,
            "work_time_ms": work_time_ms,
            "reason": str(exception)
        }), 500


@app.route("/abort", methods=["POST"])
def abort():
    global NODE_ACTIVE

    if not NODE_ACTIVE:
        return jsonify({
            "node": NODE_ID,
            "ack": False,
            "reason": "Node is down"
        }), 503

    data = request.get_json() or {}

    tx_id = data.get("transaction_id") or data.get("tx_id")
    latency_ms = float(data.get("latency_ms", 0))

    simulate_latency(latency_ms)

    work_start = time.perf_counter()

    try:
        with get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE pending_transactions
                SET status = ?
                WHERE tx_id = ?
                """,
                ("ABORTED", tx_id)
            )

            connection.commit()

            log_event(
                tx_id,
                "ABORT",
                "ACK",
                f"Node {NODE_ID} aborted or rolled back Transaction."
            )

            work_time_ms = (time.perf_counter() - work_start) * 1000
            simulate_latency(latency_ms)

            return jsonify({
                "node": NODE_ID,
                "ack": True,
                "work_time_ms": work_time_ms,
                "message": "Aborted successfully"
            })

    except Exception as exception:
        work_time_ms = (time.perf_counter() - work_start) * 1000
        simulate_latency(latency_ms)

        try:
            log_event(tx_id, "ABORT", "ERROR", str(exception))
        except Exception:
            pass

        return jsonify({
            "node": NODE_ID,
            "ack": False,
            "work_time_ms": work_time_ms,
            "reason": str(exception)
        }), 500


@app.route("/crash", methods=["POST"])
def crash():
    global NODE_ACTIVE
    NODE_ACTIVE = False

    return jsonify({
        "node": NODE_ID,
        "status": "DOWN",
        "message": f"Node {NODE_ID} is now simulated as crashed."
    })


@app.route("/recover", methods=["POST"])
def recover():
    global NODE_ACTIVE
    NODE_ACTIVE = True

    return jsonify({
        "node": NODE_ID,
        "status": "UP",
        "message": f"Node {NODE_ID} has recovered."
    })


@app.route("/accounts/<account_id>", methods=["GET"])
def get_account_info(account_id):
    if not NODE_ACTIVE:
        return jsonify({
            "node": NODE_ID,
            "status": "DOWN"
        }), 503

    with get_connection() as connection:
        account = get_account(connection, account_id)

        if account is None:
            return jsonify({
                "node": NODE_ID,
                "found": False,
                "message": "Account not found in this node."
            }), 404

        return jsonify({
            "node": NODE_ID,
            "found": True,
            "account_id": account["account_id"],
            "balance": account["balance"]
        })


@app.route("/logs", methods=["GET"])
def logs():
    if not NODE_ACTIVE:
        return jsonify({
            "node": NODE_ID,
            "status": "DOWN"
        }), 503

    limit = int(request.args.get("limit", 20))

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT id, tx_id, phase, decision, message, created_at
            FROM transaction_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = cursor.fetchall()

    return jsonify({
        "node": NODE_ID,
        "logs": [dict(row) for row in rows]
    })


def parse_arguments():
    parser = argparse.ArgumentParser(description="Participant Node Server")
    parser.add_argument("--node", required=True, choices=["A", "B", "C"], help="Node ID")
    parser.add_argument("--port", required=True, type=int, help="Port number")
    return parser.parse_args()


def main():
    global NODE_ID, DB_PATH

    args = parse_arguments()

    NODE_ID = args.node
    DB_PATH = NODE_DATABASES[NODE_ID]

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy database {DB_PATH}. Hãy chạy python nodes/init_nodes.py trước."
        )

    print(f"Starting Node {NODE_ID}")
    print(f"Database: {DB_PATH}")
    print(f"Port: {args.port}")

    app.run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()