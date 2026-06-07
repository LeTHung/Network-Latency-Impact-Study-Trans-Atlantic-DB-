from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
RAW_FILE = BASE_DIR / "benchmark" / "results_raw.csv"
SUMMARY_FILE = BASE_DIR / "benchmark" / "results_summary.csv"
CHART_DIR = BASE_DIR / "analysis" / "charts"

CHART_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    if not RAW_FILE.exists() or RAW_FILE.stat().st_size == 0:
        raise FileNotFoundError("Chưa có benchmark/results_raw.csv hoặc file đang rỗng.")

    raw = pd.read_csv(RAW_FILE)

    if SUMMARY_FILE.exists() and SUMMARY_FILE.stat().st_size > 0:
        summary = pd.read_csv(SUMMARY_FILE)
    else:
        summary = build_summary(raw)

    return raw, summary


def build_summary(raw):
    valid = raw.dropna(subset=["total_time_ms"]).copy()

    rows = []

    for latency, group in valid.groupby("latency_ms"):
        total = len(group)
        failed = (group["status"] != "SUCCESS").sum()

        rows.append({
            "latency_ms": latency,
            "transactions": total,
            "abort_rate_percent": failed / total * 100,
            "mean_total_time_ms": group["total_time_ms"].mean(),
            "median_total_time_ms": group["total_time_ms"].median(),
            "p99_total_time_ms": group["total_time_ms"].quantile(0.99),
            "mean_doing_work_ms": group["doing_work_ms"].mean(),
            "mean_network_wait_ms": group["network_wait_ms"].mean(),
            "mean_coordination_cost_percent": group["coordination_cost_percent"].mean(),
        })

    summary = pd.DataFrame(rows).sort_values("latency_ms")
    summary.to_csv(SUMMARY_FILE, index=False, encoding="utf-8-sig")

    return summary


def chart_total_time(summary):
    labels = summary["latency_ms"].astype(int).astype(str)

    plt.figure(figsize=(8, 5))
    plt.bar(labels, summary["mean_total_time_ms"])
    plt.xlabel("Network Latency (ms)")
    plt.ylabel("Mean Total Transaction Time (ms)")
    plt.title("Total Transaction Time by Network Latency")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "total_time_by_latency.png", dpi=300)
    plt.close()


def chart_coordination_cost(summary):
    labels = summary["latency_ms"].astype(int).astype(str)

    plt.figure(figsize=(8, 5))
    plt.bar(labels, summary["mean_coordination_cost_percent"])
    plt.xlabel("Network Latency (ms)")
    plt.ylabel("Mean Cost of Coordination (%)")
    plt.title("Cost of Coordination by Network Latency")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "coordination_cost.png", dpi=300)
    plt.close()


def chart_work_vs_network(summary):
    labels = summary["latency_ms"].astype(int).astype(str)

    plt.figure(figsize=(8, 5))
    plt.bar(labels, summary["mean_doing_work_ms"], label="Doing Work")
    plt.bar(
        labels,
        summary["mean_network_wait_ms"],
        bottom=summary["mean_doing_work_ms"],
        label="Network Waiting",
    )

    plt.xlabel("Network Latency (ms)")
    plt.ylabel("Mean Time (ms)")
    plt.title("Doing Work vs Network Waiting Time")
    plt.legend()
    plt.tight_layout()
    plt.savefig(CHART_DIR / "work_vs_network.png", dpi=300)
    plt.close()


def chart_mean_median_p99(summary):
    plot_df = summary[
        [
            "latency_ms",
            "mean_total_time_ms",
            "median_total_time_ms",
            "p99_total_time_ms",
        ]
    ].copy()

    plot_df["latency_ms"] = plot_df["latency_ms"].astype(int).astype(str)

    plot_df = plot_df.rename(columns={
        "mean_total_time_ms": "Mean",
        "median_total_time_ms": "Median",
        "p99_total_time_ms": "P99",
    })

    plot_df = plot_df.set_index("latency_ms")

    plot_df.plot(kind="bar", figsize=(9, 5))

    plt.xlabel("Network Latency (ms)")
    plt.ylabel("Total Transaction Time (ms)")
    plt.title("Mean, Median and P99 Transaction Time")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(CHART_DIR / "mean_median_p99.png", dpi=300)
    plt.close()


def main():
    raw, summary = load_data()

    chart_total_time(summary)
    chart_coordination_cost(summary)
    chart_work_vs_network(summary)
    chart_mean_median_p99(summary)

    print("Analysis completed.")
    print(f"Raw data: {RAW_FILE}")
    print(f"Summary: {SUMMARY_FILE}")
    print(f"Charts folder: {CHART_DIR}")

    print("\nSummary:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
