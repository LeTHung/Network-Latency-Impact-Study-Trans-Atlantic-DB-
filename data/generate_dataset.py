import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

ACCOUNTS_FILE = BASE_DIR / "accounts.csv"
TRANSACTIONS_FILE = BASE_DIR / "financial_transactions.csv"

random.seed(42)

NUM_ACCOUNTS = 1000
NUM_TRANSACTIONS = 10000

NODES = ["A", "B", "C"]


def get_node_for_account(account_number: int) -> str:
    """
    Horizontal fragmentation strategy:
    Account is assigned to Node A/B/C based on account_number % 3.
    """
    return NODES[account_number % 3]


def generate_accounts():
    accounts = []

    for i in range(1, NUM_ACCOUNTS + 1):
        account_id = f"ACC{i:04d}"
        balance = round(random.uniform(1000, 100000), 2)
        node = get_node_for_account(i)

        accounts.append({
            "account_id": account_id,
            "balance": balance,
            "node": node
        })

    with open(ACCOUNTS_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["account_id", "balance", "node"])
        writer.writeheader()
        writer.writerows(accounts)

    return accounts


def generate_transactions(accounts):
    transactions = []
    start_time = datetime(2024, 1, 1, 0, 0, 0)

    for i in range(1, NUM_TRANSACTIONS + 1):
        from_account = random.choice(accounts)
        to_account = random.choice(accounts)

        while to_account["account_id"] == from_account["account_id"]:
            to_account = random.choice(accounts)

        amount = round(random.uniform(10, 5000), 2)
        timestamp = start_time + timedelta(minutes=i)

        transaction = {
            "transaction_id": f"TX{i:06d}",
            "from_account": from_account["account_id"],
            "to_account": to_account["account_id"],
            "amount": amount,
            "transaction_type": "TRANSFER",
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "from_node": from_account["node"],
            "to_node": to_account["node"],
            "status": "PENDING"
        }

        transactions.append(transaction)

    with open(TRANSACTIONS_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "transaction_id",
                "from_account",
                "to_account",
                "amount",
                "transaction_type",
                "timestamp",
                "from_node",
                "to_node",
                "status"
            ]
        )
        writer.writeheader()
        writer.writerows(transactions)


def main():
    accounts = generate_accounts()
    generate_transactions(accounts)

    print("Dataset generated successfully.")
    print(f"Accounts file: {ACCOUNTS_FILE}")
    print(f"Transactions file: {TRANSACTIONS_FILE}")
    print(f"Total accounts: {NUM_ACCOUNTS}")
    print(f"Total transactions: {NUM_TRANSACTIONS}")


if __name__ == "__main__":
    main()