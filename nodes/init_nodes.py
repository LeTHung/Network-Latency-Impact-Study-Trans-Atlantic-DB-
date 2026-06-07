import csv
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
NODES_DIR = BASE_DIR / "nodes"

ACCOUNTS_FILE = DATA_DIR / "accounts.csv"

NODE_DATABASES = {
    "A": NODES_DIR / "node_a.db",
    "B": NODES_DIR / "node_b.db",
    "C": NODES_DIR / "node_c.db",
}


def create_connection(db_path: Path):
    return sqlite3.connect(db_path)


def create_tables(connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_id TEXT PRIMARY KEY,
            balance REAL NOT NULL,
            node TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_transactions (
            tx_id TEXT PRIMARY KEY,
            from_account TEXT,
            to_account TEXT,
            amount REAL,
            role TEXT,
            status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transaction_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_id TEXT,
            phase TEXT,
            decision TEXT,
            message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()


def reset_tables(connection):
    cursor = connection.cursor()
    cursor.execute("DELETE FROM accounts")
    cursor.execute("DELETE FROM pending_transactions")
    cursor.execute("DELETE FROM transaction_log")
    connection.commit()


def insert_account(connection, account_id: str, balance: float, node: str):
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO accounts (account_id, balance, node)
        VALUES (?, ?, ?)
        """,
        (account_id, balance, node)
    )
    connection.commit()


def initialize_node_databases():
    if not ACCOUNTS_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file {ACCOUNTS_FILE}. Hãy chạy python data/generate_dataset.py trước."
        )

    connections = {}

    try:
        for node, db_path in NODE_DATABASES.items():
            connection = create_connection(db_path)
            create_tables(connection)
            reset_tables(connection)
            connections[node] = connection

        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                account_id = row["account_id"]
                balance = float(row["balance"])
                node = row["node"]

                if node not in connections:
                    raise ValueError(f"Node không hợp lệ trong accounts.csv: {node}")

                insert_account(connections[node], account_id, balance, node)

        for node, connection in connections.items():
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM accounts")
            count = cursor.fetchone()[0]
            print(f"Node {node}: {count} accounts -> {NODE_DATABASES[node]}")

        print("Participant Node databases initialized successfully.")

    finally:
        for connection in connections.values():
            connection.close()


if __name__ == "__main__":
    initialize_node_databases()
