# Trans-Atlantic DB: Network Latency Impact Study

Đồ án mô phỏng một hệ cơ sở dữ liệu phân tán xử lý giao dịch chuyển tiền bằng giao thức **Two-Phase Commit (2PC)**. Mục tiêu là đo tác động của **network latency** đến thời gian xử lý transaction và tính **Cost of Coordination**: phần thời gian hệ thống phải chờ truyền thông mạng so với thời gian xử lý thực tế.

## 1. Thông tin đề tài

| Mục        | Nội dung                                                   |
| ---------- | ---------------------------------------------------------- |
| Project ID | #93 - Network Latency Impact Study: "Trans-Atlantic DB"    |
| Môn học    | Cơ sở dữ liệu phân tán                                     |
| Chủ đề     | Network latency, distributed transaction, Two-Phase Commit |
| Dataset    | Financial transactions, 10,000 records                     |
| Sinh viên  | Lê Tiến Hưng                                               |

## 2. Mục tiêu hệ thống

- Mô phỏng một distributed database gồm 1 Coordinator và 3 Participant Node.
- Lưu dữ liệu cục bộ trên từng node bằng SQLite.
- Cài đặt giao thức Two-Phase Commit để đảm bảo transaction cùng `COMMIT` hoặc cùng `ABORT`.
- Mô phỏng network latency ở 3 mức: `1ms`, `50ms`, `250ms`.
- Chạy benchmark nhiều lần để tính `Mean`, `Median`, `P99`, `Abort Rate` và `Cost of Coordination`.
- Mô phỏng failure scenario: kill Node B và quan sát Coordinator quyết định `GLOBAL ABORT`.

## 3. Kiến trúc hệ thống

```text
Client / Benchmark
        |
        v
Coordinator Server
        |
        +------ Node A - SQLite node_a.db
        +------ Node B - SQLite node_b.db
        +------ Node C - SQLite node_c.db
```

| Thành phần         | Vai trò                                                                     |
| ------------------ | --------------------------------------------------------------------------- |
| Client / Benchmark | Gửi transaction và cấu hình latency                                         |
| Coordinator        | Điều phối 2PC, gửi PREPARE/COMMIT/ABORT, ghi metric                         |
| Node A/B/C         | Lưu dữ liệu cục bộ, kiểm tra account, cập nhật balance, ghi transaction log |
| SQLite             | Database cục bộ của từng node                                               |

Các tiến trình giao tiếp qua HTTP REST API trên localhost.

## 4. Dataset và phân mảnh

Dataset nằm trong thư mục `data/`:

```text
data/
├── accounts.csv
├── financial_transactions.csv
└── generate_dataset.py
```

Thông tin chính:

| File                         | Nội dung                                             |
| ---------------------------- | ---------------------------------------------------- |
| `accounts.csv`               | 1,000 tài khoản, gồm `account_id`, `balance`, `node` |
| `financial_transactions.csv` | 10,000 giao dịch tài chính                           |
| `generate_dataset.py`        | Script sinh dataset                                  |

Hệ thống dùng **Horizontal Fragmentation** theo `account_id`:

```text
account_number % 3 == 0 -> Node A
account_number % 3 == 1 -> Node B
account_number % 3 == 2 -> Node C
```

Sau khi chạy `nodes/init_nodes.py`, dữ liệu được nạp vào:

```text
nodes/node_a.db
nodes/node_b.db
nodes/node_c.db
```

## 5. Two-Phase Commit

Mỗi transaction đi qua 2 phase:

| Phase            | Mô tả                                                                    |
| ---------------- | ------------------------------------------------------------------------ |
| PREPARE / VOTING | Coordinator hỏi từng node có sẵn sàng commit không                       |
| COMMIT / ABORT   | Nếu tất cả vote `YES` thì commit, nếu có lỗi/vote `NO`/timeout thì abort |

Luồng xử lý:

1. Client gửi transaction đến Coordinator qua `/transaction`.
2. Coordinator gửi `/prepare` đến Node A, Node B, Node C.
3. Mỗi node kiểm tra dữ liệu cục bộ và trả vote `YES` hoặc `NO`.
4. Coordinator tổng hợp vote.
5. Nếu tất cả `YES`, Coordinator gửi `/commit`.
6. Nếu có lỗi, Coordinator gửi `/abort`.
7. Coordinator ghi metric vào `coordinator/coordinator_log.csv`.

## 6. Mô phỏng latency

Độ trễ mạng được mô phỏng bằng `sleep()` trong code node:

```python
time.sleep(latency_ms / 1000)
```

Ba mức latency được benchmark:

| Latency | Ý nghĩa                 |
| ------: | ----------------------- |
|     1ms | Local                   |
|    50ms | Regional                |
|   250ms | Global / Trans-Atlantic |

## 7. Metric và công thức

Đồ án liên hệ với mô hình chi phí trong cơ sở dữ liệu phân tán:

```text
Cost = IO + CPU + Comm
```

Trong thí nghiệm này, dataset, số node, database engine và transaction logic được giữ cố định. Biến thay đổi chính là `Network Latency`, làm tăng thành phần `Comm`.

Các metric chính:

| Metric                      | Ý nghĩa                           |
| --------------------------- | --------------------------------- |
| `total_time_ms`             | Tổng thời gian xử lý transaction  |
| `prepare_phase_ms`          | Thời gian phase PREPARE           |
| `decision_phase_ms`         | Thời gian phase COMMIT hoặc ABORT |
| `doing_work_ms`             | Thời gian xử lý thực tế tại node  |
| `network_wait_ms`           | Thời gian chờ mạng                |
| `coordination_cost_percent` | Tỷ lệ chi phí điều phối           |

Công thức:

```text
Network Waiting Time = Total Transaction Time - Doing Work Time

Cost of Coordination (%) =
    Network Waiting Time / Total Transaction Time * 100
```

Vì các node xử lý song song, `doing_work_ms` được tính theo node chậm nhất trong từng phase, sau đó cộng phase PREPARE và phase DECISION.

## 8. Cấu trúc thư mục

```text
trans-atlantic-db/
├── analysis/
│   ├── analyze_results.py
│   └── charts/
├── benchmark/
│   ├── run_benchmark.py
│   ├── results_raw.csv
│   └── results_summary.csv
├── coordinator/
│   └── coordinator.py
├── data/
│   ├── accounts.csv
│   ├── financial_transactions.csv
│   └── generate_dataset.py
├── docs/
│   ├── proposal.docx
│   ├── design_document.docx
│   └── analysis_report.docx
├── nodes/
│   ├── init_nodes.py
│   └── node_server.py
├── README.md
├── requirements.txt
└── .gitignore
```

## 9. Cài đặt

Tạo virtual environment:

```powershell
python -m venv venv
```

Kích hoạt môi trường:

```powershell
venv\Scripts\Activate.ps1
```

Cài thư viện:

```powershell
pip install -r requirements.txt
```

Thư viện sử dụng:

```text
flask
requests
pandas
numpy
matplotlib
```

## 10. Chạy hệ thống

### Bước 1: Tạo dataset

```powershell
python data/generate_dataset.py
```

### Bước 2: Khởi tạo database cho các node

```powershell
python nodes/init_nodes.py
```

Kết quả mong đợi:

```text
Node A: 333 accounts
Node B: 334 accounts
Node C: 333 accounts
```

### Bước 3: Chạy 3 participant node

Mở 3 terminal riêng:

```powershell
python nodes/node_server.py --node A --port 5001
```

```powershell
python nodes/node_server.py --node B --port 5002
```

```powershell
python nodes/node_server.py --node C --port 5003
```

### Bước 4: Chạy Coordinator

Mở terminal thứ 4:

```powershell
python coordinator/coordinator.py --port 8000
```

### Bước 5: Kiểm tra trạng thái

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health"
Invoke-RestMethod -Uri "http://localhost:8000/nodes/health"
```

## 11. Gửi transaction thủ công

```powershell
$tx = @{
    transaction_id = "TX_DEMO_001"
    from_account = "ACC0001"
    to_account = "ACC0002"
    amount = 10
    latency_ms = 50
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://localhost:8000/transaction" `
    -Method POST `
    -ContentType "application/json" `
    -Body $tx
```

Kết quả thành công sẽ có:

```text
decision: COMMIT
status: SUCCESS
prepare_phase_ms
decision_phase_ms
total_time_ms
network_wait_ms
coordination_cost_percent
```

## 12. Chạy benchmark

Trước khi benchmark, reset database:

```powershell
python nodes/init_nodes.py
```

Sau đó chạy lại Node A, Node B, Node C và Coordinator.

Chạy benchmark:

```powershell
python benchmark/run_benchmark.py --latency 1 --runs 5 --transactions 100 --reset
python benchmark/run_benchmark.py --latency 50 --runs 5 --transactions 100
python benchmark/run_benchmark.py --latency 250 --runs 5 --transactions 100
```

Lưu ý: chỉ dùng `--reset` ở lệnh đầu tiên để không xóa kết quả benchmark của các mức latency trước.

Kết quả được lưu tại:

```text
benchmark/results_raw.csv
benchmark/results_summary.csv
```

Tổng số transaction đo chính thức:

```text
3 latency levels x 5 runs x 100 transactions = 1500 transactions
```

## 13. Phân tích và vẽ biểu đồ

```powershell
python analysis/analyze_results.py
```

Biểu đồ được tạo trong:

```text
analysis/charts/
```

| Chart                       | Ý nghĩa                                  |
| --------------------------- | ---------------------------------------- |
| `total_time_by_latency.png` | Mean total transaction time theo latency |
| `coordination_cost.png`     | Cost of Coordination theo latency        |
| `work_vs_network.png`       | Doing Work vs Network Waiting            |
| `mean_median_p99.png`       | Mean, Median và P99                      |

## 14. Kết quả benchmark

Kết quả tổng hợp từ `benchmark/results_summary.csv`:

| Latency | Transactions | Success | Abort Rate | Mean Total Time | Median Total Time | P99 Total Time | Mean Doing Work | Mean Network Waiting | Cost of Coordination |
| ------: | -----------: | ------: | ---------: | --------------: | ----------------: | -------------: | --------------: | -------------------: | -------------------: |
|     1ms |          500 |     500 |      0.00% |        57.97 ms |          56.94 ms |       99.21 ms |        23.25 ms |             34.72 ms |               58.70% |
|    50ms |          500 |     500 |      0.00% |       253.30 ms |         250.62 ms |      288.27 ms |        24.38 ms |            228.92 ms |               90.37% |
|   250ms |          500 |     500 |      0.00% |      1057.85 ms |        1053.50 ms |     1115.83 ms |        28.33 ms |           1029.52 ms |               97.33% |

Nhận xét chính:

- Khi latency tăng từ `1ms` lên `250ms`, mean total transaction time tăng khoảng `18.25` lần.
- Doing Work Time gần như ổn định, chỉ tăng nhẹ từ `23.25 ms` lên `28.33 ms`.
- Network Waiting Time tăng mạnh từ `34.72 ms` lên `1029.52 ms`.
- Cost of Coordination tăng từ `58.70%` lên `97.33%`.

Điều này chứng minh trong 2PC, khi độ trễ mạng cao, phần lớn thời gian transaction nằm ở chi phí truyền thông và điều phối giữa các node.

## 15. Failure Scenario: Kill Node B

Mô phỏng Node B bị lỗi:

```powershell
Invoke-RestMethod -Uri "http://localhost:5002/crash" -Method POST
```

Gửi một transaction mới qua Coordinator:

```powershell
$txFail = @{
    transaction_id = "TX_FAIL_NODE_B"
    from_account = "ACC0001"
    to_account = "ACC0002"
    amount = 10
    latency_ms = 50
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://localhost:8000/transaction" `
    -Method POST `
    -ContentType "application/json" `
    -Body $txFail
```

Kết quả mong đợi:

```text
decision: ABORT
status: FAILED
failed_nodes: Node B
```

Khôi phục Node B:

```powershell
Invoke-RestMethod -Uri "http://localhost:5002/recover" -Method POST
```

Kịch bản này chứng minh hệ thống không xảy ra partial commit khi một participant node bị lỗi.

## 16. Kết luận

Dự án đã mô phỏng thành công một hệ cơ sở dữ liệu phân tán sử dụng Two-Phase Commit. Kết quả benchmark cho thấy khi network latency tăng, thành phần `Comm` trong mô hình `Cost = IO + CPU + Comm` trở thành yếu tố chi phối tổng thời gian xử lý transaction. Đây là minh chứng trực tiếp cho tác động của network latency đến hiệu năng distributed transaction.
