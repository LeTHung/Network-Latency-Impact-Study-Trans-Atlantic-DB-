# Trans-Atlantic DB – Network Latency Impact Study

## 1. Thông tin tổng quan dự án

**Project ID:** #93  
**Tên đề tài:** Network Latency Impact Study: “Trans-Atlantic DB”  
**Tên đề xuất:** Evaluating Network Latency Impact on Distributed Transactions Using Two-Phase Commit  
**Môn học:** Cơ sở dữ liệu phân tán  
**Ngày thi / trình bày:** 09/06  
**Dataset:** Financial_Transactions – 10.000 bản ghi  
**Mục tiêu điểm:** Excellent 90–100%

Dự án này nghiên cứu tác động của **độ trễ mạng** đến thời gian thực thi giao dịch phân tán trong một hệ cơ sở dữ liệu phân tán mô phỏng. Hệ thống sử dụng giao thức **Two-Phase Commit – 2PC** để đảm bảo các node cùng commit hoặc cùng abort khi thực hiện giao dịch.

Trọng tâm của đồ án không chỉ là viết chương trình chạy được, mà còn phải đo đạc, phân tích và chứng minh bằng số liệu rằng khi độ trễ mạng tăng, **Communication Cost** trở thành thành phần chi phí chi phối tổng thời gian giao dịch.

---

## 2. Vấn đề nghiên cứu

Trong hệ cơ sở dữ liệu phân tán, dữ liệu có thể nằm ở nhiều site/node khác nhau. Khi một giao dịch cần cập nhật dữ liệu trên nhiều node, hệ thống phải phối hợp các node để đảm bảo tính nhất quán.

Ví dụ:

```text
Chuyển tiền từ tài khoản ACC0001 sang ACC0500
```

Nếu tài khoản gửi nằm ở Node A và tài khoản nhận nằm ở Node B, hệ thống phải đảm bảo:

```text
Hoặc cả Node A và Node B đều commit
Hoặc cả Node A và Node B đều abort
```

Không được xảy ra trường hợp:

```text
Node A trừ tiền rồi nhưng Node B chưa cộng tiền
```

Đây là bài toán đảm bảo **Atomicity** trong giao dịch phân tán.

---

## 3. Câu hỏi nghiên cứu chính

Dự án cần trả lời các câu hỏi sau:

1. Độ trễ mạng ảnh hưởng như thế nào đến tổng thời gian giao dịch 2PC?
2. Khi latency tăng từ 1ms lên 50ms và 250ms, thời gian chờ mạng chiếm bao nhiêu phần trăm tổng thời gian giao dịch?
3. Cost of Coordination thay đổi ra sao theo từng mức latency?
4. Khi một node bị lỗi, ví dụ kill Node B, giao thức 2PC xử lý như thế nào?
5. Kết quả thực nghiệm có liên hệ gì với mô hình chi phí của Özsu và Valduriez: `Cost = IO + CPU + Comm`?

---

## 4. Yêu cầu chính từ giảng viên

### 4.1. Dataset

Sử dụng dataset:

```text
Financial_Transactions – 10.000 records
```

Dataset cần có các thông tin phục vụ giao dịch tài chính, ví dụ:

| Trường | Ý nghĩa |
|---|---|
| transaction_id | Mã giao dịch |
| from_account | Tài khoản gửi |
| to_account | Tài khoản nhận |
| amount | Số tiền |
| transaction_type | Loại giao dịch |
| timestamp | Thời gian |
| from_node | Node chứa tài khoản gửi |
| to_node | Node chứa tài khoản nhận |
| status | Trạng thái giao dịch |

---

### 4.2. Mô phỏng latency

Phải mô phỏng 3 mức độ trễ mạng:

| Latency | Ý nghĩa |
|---:|---|
| 1ms | Local |
| 50ms | Regional |
| 250ms | Global / Trans-Atlantic |

Có thể dùng:

```python
time.sleep(latency_ms / 1000)
```

hoặc dùng công cụ Linux như `tc`.

Trong đồ án này, hướng triển khai ưu tiên là dùng `sleep()` trong code để dễ chạy, dễ demo và dễ kiểm soát biến thí nghiệm.

---

### 4.3. Phân tích 2PC dưới các mức latency

Phải chạy giao dịch phân tán bằng giao thức **Two-Phase Commit** ở cả 3 mức latency:

```text
1ms, 50ms, 250ms
```

Sau đó đo thời gian và so sánh.

---

### 4.4. Metric bắt buộc: Cost of Coordination

Metric quan trọng nhất là:

```text
Cost of Coordination
```

Công thức:

```text
Total Transaction Time = Doing Work Time + Network Waiting Time
```

```text
Cost of Coordination (%) = Network Waiting Time / Total Transaction Time × 100
```

Ý nghĩa:

> Cost of Coordination cho biết bao nhiêu phần trăm tổng thời gian giao dịch bị tiêu tốn cho việc chờ mạng và phối hợp giữa các node, thay vì xử lý dữ liệu thực sự.

---

## 5. Deliverables cần nộp

Theo checklist của giảng viên, nhóm cần nộp:

1. **Project Proposal** theo template.
2. **2-page Design Document**.
3. **Code Repository** trên GitHub/GitLab, có README rõ ràng.
4. **Analysis Report** giải thích thiết kế và kết quả theo lý thuyết Özsu và Valduriez.
5. **Proof Video 3–5 phút** chứng minh hệ thống chạy với dataset cụ thể và có failure scenario, ví dụ kill Node B.

Ngoài ra, sinh viên phải tham gia buổi thi cuối kỳ và trình bày sản phẩm.

---

## 6. Tiêu chí Excellent 90–100%

Để đạt mức Excellent, đồ án cần đảm bảo:

| Tiêu chí | Cách đạt Excellent |
|---|---|
| Methodology | Kiểm soát biến chặt chẽ, chạy nhiều lần, có warm-up |
| Visual Analysis | Có biểu đồ rõ ràng, chuyên nghiệp, có nhãn trục |
| Statistical Rigor | Có Mean, Median, P99 |
| Textbook Link | Liên hệ rõ với mô hình `Cost = IO + CPU + Comm` |
| Failure Proof | Có demo kill Node B và hệ thống abort đúng |
| Code Quality | Repo sạch, README rõ, chạy được theo hướng dẫn |
| Dataset | Có 10.000 records, schema hợp lý |
| Analysis | Có phân tích kết quả, không chỉ đưa bảng số |

---

## 7. Kiến thức cần nắm

### 7.1. Distributed Database

Cơ sở dữ liệu phân tán là hệ thống mà dữ liệu được lưu trên nhiều site/node khác nhau. Các node có thể nằm cùng máy, cùng mạng LAN hoặc ở các khu vực địa lý xa nhau.

Trong đồ án này, ta mô phỏng 3 node:

```text
Node A
Node B
Node C
```

Mỗi node có database riêng.

---

### 7.2. Distributed Transaction

Giao dịch phân tán là giao dịch cần thao tác trên nhiều node.

Ví dụ:

```text
Tài khoản gửi nằm ở Node A
Tài khoản nhận nằm ở Node C
```

Khi chuyển tiền, cả Node A và Node C phải phối hợp với nhau.

---

### 7.3. Atomicity

Atomicity nghĩa là giao dịch phải có tính nguyên tử:

```text
Hoặc tất cả thành công
Hoặc tất cả thất bại
```

Trong giao dịch phân tán, atomicity khó hơn vì mỗi node có thể thành công hoặc thất bại riêng.

---

### 7.4. Two-Phase Commit – 2PC

2PC là giao thức dùng để đảm bảo các node trong giao dịch phân tán cùng commit hoặc cùng abort.

Gồm 2 pha:

#### Phase 1: Prepare / Voting

Coordinator hỏi tất cả node:

```text
Bạn có sẵn sàng commit không?
```

Node trả lời:

```text
YES hoặc NO
```

#### Phase 2: Commit / Abort

Nếu tất cả node trả lời YES:

```text
Coordinator gửi COMMIT
```

Nếu có một node trả lời NO hoặc timeout:

```text
Coordinator gửi ABORT
```

---

### 7.5. Network Latency

Network latency là độ trễ truyền thông giữa các node.

Trong đồ án:

| Mức | Mô phỏng |
|---|---|
| Local | 1ms |
| Regional | 50ms |
| Global | 250ms |

2PC nhạy với latency vì phải gửi nhiều thông điệp giữa Coordinator và Participants.

---

### 7.6. Özsu và Valduriez Cost Model

Mô hình chi phí:

```text
Cost = IO + CPU + Comm
```

Trong đó:

| Thành phần | Ý nghĩa |
|---|---|
| IO | Chi phí đọc/ghi dữ liệu |
| CPU | Chi phí xử lý |
| Comm | Chi phí truyền thông mạng |

Trong thí nghiệm này:

```text
IO gần như cố định
CPU gần như cố định
Comm thay đổi theo latency
```

Do đó, khi latency tăng, `Comm` tăng mạnh và làm tổng chi phí giao dịch tăng.

---

## 8. Kiến trúc hệ thống đề xuất

Mô hình tổng quát:

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

### Thành phần

| Thành phần | Vai trò |
|---|---|
| Client / Benchmark Script | Gửi nhiều giao dịch để đo thời gian |
| Coordinator | Điều phối giao thức 2PC |
| Node A/B/C | Lưu dữ liệu cục bộ, xử lý prepare/commit/abort |
| SQLite | Database riêng cho từng node |
| Logger | Ghi log và kết quả benchmark |
| Analysis Script | Tính thống kê và vẽ biểu đồ |

---

## 9. Cấu trúc thư mục project

Cấu trúc đề xuất:

```text
trans-atlantic-db/
│
├── data/
│   ├── generate_dataset.py
│   ├── accounts.csv
│   └── financial_transactions.csv
│
├── nodes/
│   ├── node_server.py
│   ├── init_nodes.py
│   ├── node_a.db
│   ├── node_b.db
│   └── node_c.db
│
├── coordinator/
│   └── coordinator.py
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

## 10. Tech stack

| Phần | Công nghệ |
|---|---|
| Programming Language | Python |
| API Framework | Flask |
| Inter-node Communication | HTTP/REST |
| Local Storage | SQLite |
| Benchmark | Python script |
| Data Analysis | Pandas, NumPy |
| Visualization | Matplotlib |
| Deployment | Localhost processes |

---

## 11. API của Participant Node

Mỗi node cần có các endpoint:

| Method | Endpoint | Chức năng |
|---|---|---|
| GET | `/health` | Kiểm tra node còn hoạt động |
| POST | `/prepare` | Xử lý pha prepare |
| POST | `/commit` | Commit giao dịch |
| POST | `/abort` | Abort/Rollback giao dịch |
| POST | `/crash` | Mô phỏng node bị lỗi |
| POST | `/recover` | Khôi phục node |

---

## 12. API của Coordinator

Coordinator cần có các endpoint:

| Method | Endpoint | Chức năng |
|---|---|---|
| GET | `/health` | Kiểm tra coordinator |
| POST | `/transaction` | Nhận transaction và chạy 2PC |
| POST | `/benchmark-transaction` | Chạy transaction phục vụ benchmark |
| GET | `/logs` | Xem log giao dịch |

---

## 13. Luồng xử lý 2PC

### 13.1. Transaction bình thường

```text
Client gửi transaction đến Coordinator
Coordinator gửi PREPARE đến Node A/B/C
Các node kiểm tra điều kiện và trả vote YES/NO
Nếu tất cả YES, Coordinator gửi COMMIT
Các node commit và trả ACK
Coordinator trả kết quả COMMIT cho Client
```

### 13.2. Transaction lỗi

```text
Client gửi transaction đến Coordinator
Coordinator gửi PREPARE đến Node A/B/C
Node B không phản hồi hoặc trả NO
Coordinator quyết định GLOBAL ABORT
Coordinator gửi ABORT đến các node còn hoạt động
Các node rollback
Coordinator trả kết quả ABORT cho Client
```

---

## 14. Mô phỏng latency

Mỗi request-response giữa Coordinator và Node được mô phỏng như sau:

```text
Coordinator -> Node: latency
Node xử lý local database
Node -> Coordinator: latency
```

Tức là một request-response có chi phí mạng xấp xỉ:

```text
2 × latency
```

Ví dụ:

| Latency | Một request-response |
|---:|---:|
| 1ms | khoảng 2ms + work time |
| 50ms | khoảng 100ms + work time |
| 250ms | khoảng 500ms + work time |

2PC có ít nhất 2 vòng request-response:

```text
Prepare round
Commit/Abort round
```

Do đó latency ảnh hưởng rất rõ đến tổng thời gian.

---

## 15. Metrics cần đo

Mỗi transaction cần ghi:

| Metric | Ý nghĩa |
|---|---|
| tx_id | Mã giao dịch |
| latency_ms | Mức latency |
| participants | Danh sách node tham gia |
| decision | COMMIT hoặc ABORT |
| total_time_ms | Tổng thời gian giao dịch |
| prepare_phase_ms | Thời gian pha prepare |
| decision_phase_ms | Thời gian pha commit/abort |
| doing_work_ms | Thời gian xử lý thật |
| network_wait_ms | Thời gian chờ mạng |
| coordination_cost_percent | Tỷ lệ chi phí phối hợp |
| status | SUCCESS/FAILED |
| failed_node | Node lỗi nếu có |

---

## 16. Công thức tính

```text
Total Transaction Time = Doing Work Time + Network Waiting Time
```

```text
Network Waiting Time = Total Transaction Time - Doing Work Time
```

```text
Cost of Coordination (%) = Network Waiting Time / Total Transaction Time × 100
```

Các thống kê:

```text
Mean = trung bình
Median = trung vị
P99 = 99th percentile / tail latency
```

---

## 17. Benchmark Methodology

Để đạt Excellent, benchmark nên làm như sau:

```text
Với mỗi mức latency: 1ms, 50ms, 250ms
- Warm-up 20 transactions
- Chạy 100 transactions
- Lặp lại 5 runs
```

Tổng số transaction đo:

```text
3 latency × 5 runs × 100 transactions = 1500 transactions
```

Kết quả cần xuất ra:

```text
results_raw.csv
results_summary.csv
```

---

## 18. Biểu đồ cần có

### 18.1. Total Transaction Time by Latency

So sánh tổng thời gian giao dịch trung bình ở 3 mức latency.

### 18.2. Coordination Cost Percentage

Cho thấy phần trăm thời gian dành cho chờ mạng/phối hợp.

### 18.3. Doing Work vs Waiting Network

Biểu đồ stacked bar, chia tổng thời gian thành:

```text
Doing Work
Waiting for Network
```

Đây là biểu đồ quan trọng nhất vì đúng yêu cầu đề.

### 18.4. Mean / Median / P99

Biểu đồ thống kê độ trễ, thể hiện cả độ trễ trung bình và tail latency.

---

## 19. Failure scenario: Kill Node B

### Mục tiêu

Chứng minh hệ thống không bị partial commit khi một node lỗi.

### Cách demo

1. Chạy Node A, Node B, Node C.
2. Chạy một transaction bình thường và cho thấy `GLOBAL COMMIT`.
3. Kill Node B bằng cách tắt terminal hoặc gọi endpoint `/crash`.
4. Chạy transaction mới.
5. Coordinator phát hiện Node B timeout.
6. Coordinator quyết định `GLOBAL ABORT`.
7. Node A và Node C rollback.
8. Log cho thấy không có partial commit.

### Log mong muốn

```text
[TX1002] PREPARE sent to A, B, C
[TX1002] Vote A = YES
[TX1002] Node B timeout
[TX1002] Vote C = YES
[TX1002] GLOBAL ABORT
[TX1002] ABORT sent to A and C
```

---

## 20. Nội dung Project Proposal

File proposal cần có:

1. Project Identity
2. Objective & Problem Statement
3. Dataset Specification
4. System Architecture
5. Tech Stack & Implementation Plan
6. Success Metrics & Analysis
7. Project Milestones

---

## 21. Nội dung 2-page Design Document

### Trang 1

1. Problem Overview
2. System Architecture Diagram
3. Dataset and Fragmentation Strategy
4. Node Responsibilities

### Trang 2

1. Two-Phase Commit Flow
2. Latency Simulation Method
3. Metrics Collection
4. Failure Handling

---

## 22. Nội dung Analysis Report

Báo cáo phân tích nên có:

1. Introduction
2. Distributed Transaction Background
3. Two-Phase Commit Protocol
4. Experimental Design
5. Benchmark Methodology
6. Results
7. Statistical Analysis
8. Failure Scenario
9. Link to Özsu and Valduriez Cost Model
10. Conclusion

Phần quan trọng nhất:

```text
According to Özsu and Valduriez, the cost of a distributed database operation can be modeled as:

Cost = IO + CPU + Comm

In this experiment, IO and CPU costs are kept nearly constant by using the same dataset, same database engine, same transaction logic, and same number of nodes. The controlled variable is network latency. As latency increases from 1ms to 50ms and 250ms, the communication component increases significantly and becomes the dominant factor in total transaction time.
```

---

## 23. Nội dung README

README trên GitHub cần có:

1. Overview
2. Project ID
3. System Architecture
4. Dataset
5. Installation
6. How to run nodes
7. How to run coordinator
8. How to run benchmark
9. How to simulate Node B failure
10. Results and charts
11. Theoretical link

---

## 24. Video proof 3–5 phút

Kịch bản video:

```text
0:00 – 0:30
Giới thiệu đề tài, dataset, mục tiêu.

0:30 – 1:00
Mở sơ đồ kiến trúc: Coordinator + Node A/B/C.

1:00 – 1:45
Chạy transaction bình thường.
Cho thấy GLOBAL COMMIT.

1:45 – 2:30
Chạy benchmark với 1ms, 50ms, 250ms.
Mở file results_summary.csv.

2:30 – 3:30
Kill Node B.
Chạy transaction mới.
Cho thấy GLOBAL ABORT.

3:30 – 4:30
Mở biểu đồ: total time, coordination cost, work vs network, P99.

4:30 – 5:00
Kết luận theo Cost = IO + CPU + Comm.
```

---

## 25. Timeline thực hiện

### Ngày 1

- Tạo project.
- Tạo dataset.
- Viết proposal.
- Viết README bản đầu.

### Ngày 2

- Viết node_server.py.
- Tạo SQLite cho Node A/B/C.
- Làm API `/health`, `/prepare`, `/commit`, `/abort`.

### Ngày 3

- Viết coordinator.py.
- Implement 2PC.
- Test transaction commit/abort.

### Ngày 4

- Thêm latency simulation.
- Đo total time, work time, network wait.
- Tính Cost of Coordination.

### Ngày 5

- Viết benchmark.
- Chạy nhiều lần.
- Xuất raw result và summary.

### Ngày 6

- Làm failure case Node B.
- Test timeout/global abort/rollback.

### Ngày 7

- Vẽ biểu đồ.
- Viết analysis report.

### Ngày 8

- Hoàn thiện README.
- Đẩy GitHub.
- Quay video proof.
- Kiểm tra toàn bộ deliverables.

### Ngày 9

- Trình bày.
- Chuẩn bị trả lời vấn đáp.

---

## 26. Câu hỏi vấn đáp thường gặp

### Câu 1. Vì sao dùng 2PC?

Vì 2PC đảm bảo atomicity trong giao dịch phân tán. Tất cả node phải cùng commit hoặc cùng abort, tránh dữ liệu không nhất quán.

### Câu 2. Vì sao latency ảnh hưởng mạnh đến 2PC?

Vì 2PC cần nhiều vòng giao tiếp giữa Coordinator và Participants. Mỗi vòng giao tiếp đều bị cộng thêm network latency.

### Câu 3. Cost of Coordination là gì?

Là tỷ lệ thời gian dùng để chờ mạng và phối hợp giữa các node so với tổng thời gian giao dịch.

### Câu 4. Khi kill Node B thì hệ thống xử lý thế nào?

Coordinator không nhận đủ vote YES nên quyết định GLOBAL ABORT. Các node còn lại rollback để tránh partial commit.

### Câu 5. Liên hệ Özsu và Valduriez ra sao?

Theo mô hình `Cost = IO + CPU + Comm`, khi IO và CPU được giữ cố định, latency tăng làm Comm tăng. Vì vậy tổng chi phí giao dịch tăng chủ yếu do Communication Cost.

---

## 27. Checklist hoàn thành đồ án

| Hạng mục | Trạng thái |
|---|---|
| Dataset 10.000 records | Chưa / Đã |
| Project Proposal | Chưa / Đã |
| Design Document 2 trang | Chưa / Đã |
| Node A/B/C | Chưa / Đã |
| Coordinator | Chưa / Đã |
| 2PC chạy được | Chưa / Đã |
| Latency simulation | Chưa / Đã |
| Benchmark nhiều lần | Chưa / Đã |
| Mean, Median, P99 | Chưa / Đã |
| Cost of Coordination | Chưa / Đã |
| Biểu đồ | Chưa / Đã |
| Failure demo Node B | Chưa / Đã |
| Analysis Report | Chưa / Đã |
| README GitHub | Chưa / Đã |
| Video proof | Chưa / Đã |

---

## 28. Kết luận định hướng

Hướng triển khai tốt nhất cho đồ án:

```text
Python + Flask
3 participant nodes
1 coordinator
SQLite riêng cho từng node
Financial_Transactions 10.000 records
Two-Phase Commit
Latency 1ms / 50ms / 250ms
Benchmark nhiều lần
Mean / Median / P99
Cost of Coordination
Failure scenario: kill Node B
Analysis theo Cost = IO + CPU + Comm
```

Nếu hoàn thành đầy đủ các phần trên, đồ án có đủ cơ sở để đạt mức **Excellent 90–100%**.
