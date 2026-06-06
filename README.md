# Trans-Atlantic DB: Network Latency Impact Study

## 1. Thông tin đồ án

**Môn học:** Cơ sở dữ liệu phân tán
**Project ID:** #93 – Network Latency Impact Study: “Trans-Atlantic DB”
**Tên đề tài:** Nghiên cứu tác động của Network Latency đến Distributed Transaction sử dụng Two-Phase Commit
**Sinh viên thực hiện:** Lê Tiến Hưng
**Hình thức:** Đồ án cá nhân

---

## 2. Giới thiệu

Đồ án này mô phỏng một hệ cơ sở dữ liệu phân tán gồm một **Coordinator** và ba **Participant Node**. Hệ thống sử dụng giao thức **Two-Phase Commit – 2PC** để xử lý **Distributed Transaction** và đảm bảo các node cùng `Commit` hoặc cùng `Abort`.

Mục tiêu chính của đồ án là đánh giá tác động của **Network Latency** đến thời gian xử lý Transaction. Khi các node nằm xa nhau hơn về mặt mạng, thời gian chờ truyền thông tăng lên, từ đó làm tăng **Communication Cost** và **Cost of Coordination**.

Đồ án mô phỏng ba mức Latency:

| Latency | Ý nghĩa                 |
| ------: | ----------------------- |
|     1ms | Local                   |
|    50ms | Regional                |
|   250ms | Global / Trans-Atlantic |

Kết quả Benchmark sẽ được phân tích dựa trên mô hình chi phí của Özsu và Valduriez:

```text
Cost = IO + CPU + Comm
```

Trong đó `Comm` là Communication Cost, thành phần bị ảnh hưởng trực tiếp bởi Network Latency.

---

## 3. Mục tiêu dự án

Dự án tập trung vào các mục tiêu sau:

1. Xây dựng hệ thống mô phỏng Distributed Database với 3 Participant Node.
2. Cài đặt giao thức Two-Phase Commit.
3. Mô phỏng Network Latency ở các mức 1ms, 50ms và 250ms.
4. Đo các metric như total transaction time, doing work time, network waiting time và Cost of Coordination.
5. Chạy Benchmark nhiều lần để tính Mean, Median và P99.
6. Mô phỏng Failure Scenario bằng cách kill Node B.
7. Phân tích kết quả dựa trên lý thuyết `Cost = IO + CPU + Comm`.

---

## 4. System Architecture

Kiến trúc tổng quát của hệ thống:

```text
Client / Benchmark Script
          |
          v
    Coordinator Server
          |
   ---------------------
   |         |         |
 Node A    Node B    Node C
 SQLite    SQLite    SQLite
```

### Thành phần chính

| Thành phần                | Vai trò                               |
| ------------------------- | ------------------------------------- |
| Client / Benchmark Script | Gửi Transaction và chạy Benchmark     |
| Coordinator               | Điều phối giao thức Two-Phase Commit  |
| Node A                    | Participant Node lưu một phần dữ liệu |
| Node B                    | Participant Node lưu một phần dữ liệu |
| Node C                    | Participant Node lưu một phần dữ liệu |
| SQLite                    | Local storage cho từng node           |

Coordinator giao tiếp với các Participant Node thông qua **HTTP/REST API**.

---

## 5. Dataset

Dự án sử dụng dataset mô phỏng dạng **Financial_Transactions**.

Dataset gồm:

- 1.000 tài khoản
- 10.000 Transaction

### Schema của Transaction

| Thuộc tính       | Ý nghĩa                  |
| ---------------- | ------------------------ |
| transaction_id   | Mã Transaction           |
| from_account     | Tài khoản gửi            |
| to_account       | Tài khoản nhận           |
| amount           | Số tiền giao dịch        |
| transaction_type | Loại giao dịch           |
| timestamp        | Thời gian phát sinh      |
| from_node        | Node chứa tài khoản gửi  |
| to_node          | Node chứa tài khoản nhận |
| status           | Trạng thái Transaction   |

### Fragmentation Strategy

Dữ liệu tài khoản được chia theo **Horizontal Fragmentation** trên ba node:

```text
account_id % 3 = 0 → Node A
account_id % 3 = 1 → Node B
account_id % 3 = 2 → Node C
```

Ví dụ:

```text
ACC0001 → Node B
ACC0002 → Node C
ACC0003 → Node A
```

Cách chia này giúp mô phỏng trường hợp một Transaction có thể liên quan đến nhiều node khác nhau.

---

## 6. Tech Stack

| Công nghệ          | Vai trò                                               |
| ------------------ | ----------------------------------------------------- |
| Python             | Ngôn ngữ lập trình chính                              |
| Flask              | Xây dựng REST API                                     |
| Requests           | Gửi HTTP request giữa Coordinator và Participant Node |
| SQLite             | Lưu trữ dữ liệu cục bộ tại từng node                  |
| Pandas             | Xử lý dữ liệu Benchmark                               |
| NumPy              | Tính toán thống kê                                    |
| Matplotlib         | Vẽ biểu đồ                                            |
| ThreadPoolExecutor | Gửi request song song đến các Participant Node        |

---

## 7. Cấu trúc thư mục

```text
trans-atlantic-db/
│
├── data/
│   ├── generate_dataset.py
│   ├── accounts.csv
│   └── financial_transactions.csv
│
├── nodes/
│   ├── init_nodes.py
│   ├── node_server.py
│   ├── node_a.db
│   ├── node_b.db
│   └── node_c.db
│
├── coordinator/
│   ├── coordinator.py
│   └── coordinator_log.csv
│
├── benchmark/
│   ├── run_benchmark.py
│   ├── results_raw.csv
│   └── results_summary.csv
│
├── analysis/
│   ├── analyze_results.py
│   └── charts/
│       ├── total_time_by_latency.png
│       ├── coordination_cost.png
│       ├── work_vs_network.png
│       └── mean_median_p99.png
│
├── docs/
│   ├── proposal.md
│   ├── design_document.md
│   ├── analysis_report.md
│   └── project_overview.md
│
├── README.md
└── requirements.txt
```

---

## 8. Cài đặt môi trường

### Bước 1: Clone repository

```bash
git clone <repository-url>
cd trans-atlantic-db
```

### Bước 2: Tạo virtual environment

Trên Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

Nếu PowerShell chặn script, chạy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\activate
```

Trên macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### Bước 3: Cài đặt thư viện

```bash
pip install -r requirements.txt
```

Nội dung `requirements.txt`:

```txt
flask
requests
pandas
numpy
matplotlib
```

---

## 9. Tạo dataset

Chạy lệnh:

```bash
python data/generate_dataset.py
```

Sau khi chạy xong, hệ thống sẽ tạo:

```text
data/accounts.csv
data/financial_transactions.csv
```

Kiểm tra số dòng Transaction:

```powershell
python -c "import pandas as pd; df=pd.read_csv('data/financial_transactions.csv'); print('Rows:', len(df)); print(df.head())"
```

Kết quả mong muốn:

```text
Rows: 10000
```

---

## 10. Khởi tạo SQLite database cho các node

Chạy lệnh:

```bash
python nodes/init_nodes.py
```

Sau khi chạy xong, hệ thống sẽ tạo SQLite database riêng cho từng node:

```text
nodes/node_a.db
nodes/node_b.db
nodes/node_c.db
```

Kết quả mong muốn:

```text
Node A: 333 accounts
Node B: 334 accounts
Node C: 333 accounts
Khởi tạo database cho các Participant Node thành công.
```

Mỗi database có các bảng chính:

| Bảng                 | Ý nghĩa                                    |
| -------------------- | ------------------------------------------ |
| accounts             | Lưu tài khoản cục bộ của node              |
| pending_transactions | Lưu Transaction đang ở trạng thái PREPARED |
| transaction_log      | Ghi log các phase PREPARE, COMMIT, ABORT   |

---

## 11. Chạy các Participant Node

Mở 3 terminal riêng.

### Terminal 1: Node A

```powershell
python nodes/node_server.py --node A --port 5001
```

### Terminal 2: Node B

```powershell
python nodes/node_server.py --node B --port 5002
```

### Terminal 3: Node C

```powershell
python nodes/node_server.py --node C --port 5003
```

Nếu chạy thành công, terminal sẽ hiển thị dạng:

```text
Starting Node A
Database: ...\nodes\node_a.db
Port: 5001
Running on http://127.0.0.1:5001
```

---

## 12. Kiểm tra trạng thái các node

Trên Windows PowerShell, nên dùng `Invoke-RestMethod` hoặc `curl.exe`.

### Cách 1: Dùng Invoke-RestMethod

```powershell
Invoke-RestMethod -Uri "http://localhost:5001/health"
Invoke-RestMethod -Uri "http://localhost:5002/health"
Invoke-RestMethod -Uri "http://localhost:5003/health"
```

### Cách 2: Dùng curl.exe

```powershell
curl.exe http://localhost:5001/health
curl.exe http://localhost:5002/health
curl.exe http://localhost:5003/health
```

Kết quả mong muốn:

```text
Node A → UP
Node B → UP
Node C → UP
```

Lưu ý: Trong PowerShell, lệnh `curl` có thể bị hiểu thành `Invoke-WebRequest` và hiện cảnh báo bảo mật. Vì vậy nên dùng `curl.exe` hoặc `Invoke-RestMethod`.

---

## 13. Kiểm tra tài khoản trong từng node

Ví dụ kiểm tra các tài khoản:

```powershell
Invoke-RestMethod -Uri "http://localhost:5001/accounts/ACC0003"
Invoke-RestMethod -Uri "http://localhost:5002/accounts/ACC0001"
Invoke-RestMethod -Uri "http://localhost:5003/accounts/ACC0002"
```

Kết quả mong muốn:

```text
ACC0003 → Node A
ACC0001 → Node B
ACC0002 → Node C
```

---

## 14. Test thủ công Two-Phase Commit trên các Participant Node

Phần này dùng để kiểm tra riêng các Participant Node trước khi chạy Coordinator.

Transaction test:

```text
from_account = ACC0001
to_account   = ACC0002
amount       = 100
```

Theo Fragmentation Strategy:

```text
ACC0001 → Node B → role DEBIT
ACC0002 → Node C → role CREDIT
Node A không liên quan → role NONE
```

### Bước 1: Tạo body Transaction

```powershell
$body = @{
    transaction_id = "TX_MANUAL_001"
    from_account = "ACC0001"
    to_account = "ACC0002"
    amount = 100
    latency_ms = 1
} | ConvertTo-Json
```

### Bước 2: Gửi PREPARE đến 3 node

```powershell
Invoke-RestMethod -Uri "http://localhost:5001/prepare" -Method POST -ContentType "application/json" -Body $body
Invoke-RestMethod -Uri "http://localhost:5002/prepare" -Method POST -ContentType "application/json" -Body $body
Invoke-RestMethod -Uri "http://localhost:5003/prepare" -Method POST -ContentType "application/json" -Body $body
```

Kết quả mong muốn:

```text
Node A → vote YES, role NONE
Node B → vote YES, role DEBIT
Node C → vote YES, role CREDIT
```

### Bước 3: Gửi COMMIT đến 3 node

```powershell
$commitBody = @{
    transaction_id = "TX_MANUAL_001"
    latency_ms = 1
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5001/commit" -Method POST -ContentType "application/json" -Body $commitBody
Invoke-RestMethod -Uri "http://localhost:5002/commit" -Method POST -ContentType "application/json" -Body $commitBody
Invoke-RestMethod -Uri "http://localhost:5003/commit" -Method POST -ContentType "application/json" -Body $commitBody
```

Kết quả mong muốn:

```text
Node A → No local change
Node B → Committed successfully, role DEBIT
Node C → Committed successfully, role CREDIT
```

---

## 15. Xem log của Participant Node

Xem log Node A:

```powershell
Invoke-RestMethod -Uri "http://localhost:5001/logs?limit=5"
```

Xem log Node B:

```powershell
Invoke-RestMethod -Uri "http://localhost:5002/logs?limit=5"
```

Xem log Node C:

```powershell
Invoke-RestMethod -Uri "http://localhost:5003/logs?limit=5"
```

Log dùng để chứng minh hệ thống đã xử lý các phase:

```text
PREPARE
COMMIT
ABORT
```

---

## 16. Chạy Coordinator

Sau khi chạy đủ Node A, Node B và Node C, mở terminal mới và chạy:

```powershell
python coordinator/coordinator.py --port 8000
```

Nếu chạy thành công:

```text
Starting Coordinator
Port: 8000
Running on http://127.0.0.1:8000
```

Kiểm tra Coordinator:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

Kiểm tra trạng thái các node thông qua Coordinator:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/nodes/health"
```

---

## 17. Gửi Transaction qua Coordinator

Khi dùng Coordinator, người dùng chỉ cần gửi một Transaction. Coordinator sẽ tự động điều phối toàn bộ Two-Phase Commit.

### Bước 1: Tạo Transaction

```powershell
$tx = @{
    transaction_id = "TX_COORD_001"
    from_account = "ACC0001"
    to_account = "ACC0002"
    amount = 100
    latency_ms = 1
} | ConvertTo-Json
```

### Bước 2: Gửi Transaction đến Coordinator

```powershell
$result = Invoke-RestMethod -Uri "http://localhost:8000/transaction" -Method POST -ContentType "application/json" -Body $tx
$result | ConvertTo-Json -Depth 10
```

Kết quả mong muốn:

```text
decision = COMMIT
status   = SUCCESS
```

Trong `prepare_results`:

```text
Node A → vote YES, role NONE
Node B → vote YES, role DEBIT
Node C → vote YES, role CREDIT
```

Trong `decision_results`:

```text
Node A → ack True, No local change
Node B → ack True, Committed successfully
Node C → ack True, Committed successfully
```

---

## 18. Metric được Coordinator đo

Mỗi Transaction qua Coordinator sẽ ghi các metric:

| Metric                    | Ý nghĩa                       |
| ------------------------- | ----------------------------- |
| transaction_id            | Mã Transaction                |
| latency_ms                | Mức Latency mô phỏng          |
| decision                  | COMMIT hoặc ABORT             |
| status                    | SUCCESS hoặc FAILED           |
| prepare_phase_ms          | Thời gian phase PREPARE       |
| decision_phase_ms         | Thời gian phase COMMIT/ABORT  |
| total_time_ms             | Tổng thời gian Transaction    |
| doing_work_ms             | Thời gian xử lý thật tại node |
| network_wait_ms           | Thời gian chờ mạng            |
| coordination_cost_percent | Cost of Coordination          |
| failed_nodes              | Node lỗi nếu có               |
| prepare_results           | Kết quả phase PREPARE         |
| decision_results          | Kết quả phase COMMIT/ABORT    |

Công thức chính:

```text
Network Waiting Time = Total Transaction Time - Doing Work Time
```

```text
Cost of Coordination (%) = Network Waiting Time / Total Transaction Time × 100
```

---

## 19. Test Latency 1ms, 50ms và 250ms

### Latency 1ms

```powershell
$tx1 = @{
    transaction_id = "TX_LATENCY_001"
    from_account = "ACC0001"
    to_account = "ACC0002"
    amount = 100
    latency_ms = 1
} | ConvertTo-Json

$result1 = Invoke-RestMethod -Uri "http://localhost:8000/transaction" -Method POST -ContentType "application/json" -Body $tx1
$result1.total_time_ms
$result1.coordination_cost_percent
```

### Latency 50ms

```powershell
$tx50 = @{
    transaction_id = "TX_LATENCY_050"
    from_account = "ACC0004"
    to_account = "ACC0005"
    amount = 100
    latency_ms = 50
} | ConvertTo-Json

$result50 = Invoke-RestMethod -Uri "http://localhost:8000/transaction" -Method POST -ContentType "application/json" -Body $tx50
$result50.total_time_ms
$result50.coordination_cost_percent
```

### Latency 250ms

```powershell
$tx250 = @{
    transaction_id = "TX_LATENCY_250"
    from_account = "ACC0007"
    to_account = "ACC0008"
    amount = 100
    latency_ms = 250
} | ConvertTo-Json

$result250 = Invoke-RestMethod -Uri "http://localhost:8000/transaction" -Method POST -ContentType "application/json" -Body $tx250
$result250.total_time_ms
$result250.coordination_cost_percent
```

Kết quả kỳ vọng:

```text
Latency 1ms   → total_time_ms thấp
Latency 50ms  → total_time_ms tăng rõ
Latency 250ms → total_time_ms tăng rất mạnh
```

---

## 20. Failure Scenario: Kill Node B

Mục tiêu của phần này là chứng minh hệ thống không bị **partial commit** khi một Participant Node bị lỗi.

### Bước 1: Cho Node B crash

```powershell
Invoke-RestMethod -Uri "http://localhost:5002/crash" -Method POST
```

Kiểm tra Node B:

```powershell
Invoke-RestMethod -Uri "http://localhost:5002/health"
```

Kết quả mong muốn:

```text
Node B → DOWN
```

### Bước 2: Gửi Transaction mới qua Coordinator

```powershell
$txFail = @{
    transaction_id = "TX_FAIL_NODE_B_001"
    from_account = "ACC0001"
    to_account = "ACC0002"
    amount = 100
    latency_ms = 1
} | ConvertTo-Json

$resultFail = Invoke-RestMethod -Uri "http://localhost:8000/transaction" -Method POST -ContentType "application/json" -Body $txFail
$resultFail | ConvertTo-Json -Depth 10
```

Kết quả mong muốn:

```text
decision = ABORT
status   = FAILED
failed_nodes có Node B
```

Ý nghĩa:

```text
Coordinator không nhận đủ vote YES
Coordinator quyết định GLOBAL ABORT
Các node còn lại thực hiện Rollback/Abort
Không xảy ra partial commit
```

### Bước 3: Khôi phục Node B

```powershell
Invoke-RestMethod -Uri "http://localhost:5002/recover" -Method POST
```

Kiểm tra lại toàn bộ node:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/nodes/health"
```

---

## 21. Xem log của Coordinator

Coordinator ghi log tại:

```text
coordinator/coordinator_log.csv
```

Xem log qua API:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/logs?limit=5"
```

Xem log dạng bảng:

```powershell
$logs = Invoke-RestMethod -Uri "http://localhost:8000/logs?limit=5"
$logs.logs | Format-Table transaction_id, latency_ms, decision, status, total_time_ms, coordination_cost_percent
```

---

## 22. Chạy Benchmark

Phần Benchmark dùng để chạy nhiều Transaction ở từng mức Latency và xuất kết quả phân tích.

Chạy Benchmark:

```powershell
python benchmark/run_benchmark.py --latency 1 --runs 5 --transactions 100
python benchmark/run_benchmark.py --latency 50 --runs 5 --transactions 100
python benchmark/run_benchmark.py --latency 250 --runs 5 --transactions 100
```

Kết quả sẽ được lưu tại:

```text
benchmark/results_raw.csv
benchmark/results_summary.csv
```

### Benchmark Methodology

Với mỗi mức Latency:

```text
Warm-up: 20 Transaction
Runs: 5
Transactions per run: 100
```

Tổng số Transaction đo:

```text
3 Latency × 5 Runs × 100 Transactions = 1500 Transactions
```

Các thống kê cần tính:

| Thống kê           | Ý nghĩa                        |
| ------------------ | ------------------------------ |
| Mean               | Giá trị trung bình             |
| Median             | Giá trị trung vị               |
| P99                | Tail latency tại percentile 99 |
| Min                | Giá trị nhỏ nhất               |
| Max                | Giá trị lớn nhất               |
| Standard Deviation | Độ lệch chuẩn                  |
| Abort Rate         | Tỷ lệ Transaction bị Abort     |

---

## 23. Phân tích kết quả và vẽ biểu đồ

Chạy lệnh:

```powershell
python analysis/analyze_results.py
```

Kết quả sẽ tạo các biểu đồ trong thư mục:

```text
analysis/charts/
```

Các biểu đồ cần có:

| Biểu đồ                   | Ý nghĩa                                     |
| ------------------------- | ------------------------------------------- |
| total_time_by_latency.png | So sánh total transaction time theo Latency |
| coordination_cost.png     | So sánh Cost of Coordination                |
| work_vs_network.png       | So sánh Doing Work và Network Waiting       |
| mean_median_p99.png       | So sánh Mean, Median và P99                 |

Biểu đồ quan trọng nhất là:

```text
Doing Work vs Network Waiting
```

Vì biểu đồ này cho thấy bao nhiêu phần thời gian là xử lý thật và bao nhiêu phần thời gian là chờ mạng.

---

## 24. Liên hệ lý thuyết Özsu và Valduriez

Theo Özsu và Valduriez, chi phí của một thao tác trong cơ sở dữ liệu phân tán có thể biểu diễn như sau:

```text
Cost = IO + CPU + Comm
```

Trong đồ án này:

| Thành phần | Ý nghĩa trong hệ thống                                  |
| ---------- | ------------------------------------------------------- |
| IO         | Chi phí đọc/ghi SQLite                                  |
| CPU        | Chi phí xử lý logic Transaction                         |
| Comm       | Communication Cost giữa Coordinator và Participant Node |

Trong thí nghiệm, các yếu tố sau được giữ gần như cố định:

```text
Dataset
Số lượng node
Database engine
Transaction logic
Cách đo metric
```

Biến được thay đổi có kiểm soát là:

```text
Network Latency
```

Do đó, khi Latency tăng, `Comm` tăng mạnh. Kết quả Benchmark dùng để chứng minh rằng Communication Cost có thể trở thành yếu tố chi phối tổng thời gian xử lý Distributed Transaction.

---

## 25. Deliverables

Các sản phẩm cần nộp cho giảng viên:

| Deliverable            | File / Link                                                  |
| ---------------------- | ------------------------------------------------------------ |
| Project Proposal       | `docs/proposal.md`                                           |
| 2-page Design Document | `docs/design_document.md`                                    |
| Code Repository        | GitHub/GitLab repository                                     |
| Analysis Report        | `docs/analysis_report.md`                                    |
| Proof Video            | Link video 3–5 phút                                          |
| Dataset                | `data/financial_transactions.csv`                            |
| Benchmark Results      | `benchmark/results_raw.csv`, `benchmark/results_summary.csv` |
| Charts                 | `analysis/charts/`                                           |

---

## 26. Proof Video 3–5 phút

Kịch bản quay video đề xuất:

```text
0:00 – 0:30
Giới thiệu đề tài, mục tiêu và kiến trúc hệ thống.

0:30 – 1:15
Chạy Node A, Node B, Node C và Coordinator.

1:15 – 2:00
Gửi một Transaction bình thường và cho thấy GLOBAL COMMIT.

2:00 – 2:45
Chạy hoặc mở kết quả Benchmark với Latency 1ms, 50ms, 250ms.

2:45 – 3:45
Kill Node B và gửi Transaction mới.
Cho thấy Coordinator quyết định GLOBAL ABORT.

3:45 – 5:00
Mở biểu đồ và kết luận theo Cost = IO + CPU + Comm.
```

---

## 27. Current Progress

- [x] Tạo cấu trúc project
- [x] Viết dataset generator
- [x] Tạo dataset Financial_Transactions
- [x] Viết Project Proposal nháp
- [x] Viết README
- [x] Khởi tạo SQLite database cho các node
- [x] Xây dựng Participant Node API
- [x] Test `/health`
- [x] Test `/prepare`
- [x] Test `/commit`
- [x] Test log của node
- [x] Xây dựng Coordinator
- [x] Implement Two-Phase Commit tự động qua Coordinator
- [x] Test Transaction qua Coordinator
- [x] Demo Failure Scenario với Node B
- [ ] Thêm Latency Simulation vào Benchmark
- [ ] Chạy Benchmark 1ms / 50ms / 250ms
- [ ] Tính Mean, Median, P99
- [ ] Tính Cost of Coordination
- [ ] Vẽ biểu đồ
- [ ] Demo Failure Scenario với Node B
- [ ] Viết Analysis Report
- [ ] Quay Proof Video

---

## 28. Trạng thái test hiện tại

Hệ thống Participant Node đã test thành công với Transaction thủ công:

```text
Transaction: TX_MANUAL_001
from_account: ACC0001
to_account: ACC0002
amount: 100
latency_ms: 1
```

Kết quả phase PREPARE:

```text
Node A → role NONE → vote YES
Node B → role DEBIT → vote YES
Node C → role CREDIT → vote YES
```

Kết quả phase COMMIT:

```text
Node A → No local change
Node B → Committed successfully
Node C → Committed successfully
```

Điều này chứng minh ba Participant Node đã xử lý đúng vai trò trong Two-Phase Commit.

---

## 29. Kết luận

Dự án mô phỏng một hệ cơ sở dữ liệu phân tán sử dụng Two-Phase Commit để xử lý Distributed Transaction. Hệ thống được thiết kế để đo tác động của Network Latency đến tổng thời gian giao dịch và Cost of Coordination.

Khi hoàn thiện Benchmark và Analysis, kết quả sẽ chứng minh rằng khi Latency tăng từ 1ms lên 50ms và 250ms, Communication Cost tăng mạnh và trở thành thành phần chi phối tổng thời gian xử lý Transaction. Đây là minh chứng thực nghiệm cho mô hình chi phí:

```text
Cost = IO + CPU + Comm
```
