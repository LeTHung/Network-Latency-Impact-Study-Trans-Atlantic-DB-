# Analysis Report: Network Latency Impact on Distributed Transactions using Two-Phase Commit

## 1. Mục Tiêu Phân Tích

Mục tiêu của báo cáo là đánh giá tác động của Network Latency đến thời gian xử lý Distributed Transaction trong hệ cơ sở dữ liệu phân tán sử dụng giao thức Two-Phase Commit (2PC).

Trong hệ thống này, Client gửi transaction đến Coordinator. Coordinator điều phối giao dịch đến ba Participant Node gồm Node A, Node B và Node C. Mỗi node lưu dữ liệu cục bộ bằng SQLite và giao tiếp với Coordinator thông qua REST API.

Thí nghiệm thay đổi Network Latency ở ba mức:

| Latency | Ý nghĩa |
|---:|---|
| 1ms | Local |
| 50ms | Regional |
| 250ms | Global / Trans-Atlantic |

Mục tiêu chính là chứng minh rằng khi Network Latency tăng, Communication Cost trong Distributed Transaction cũng tăng, từ đó làm tăng tổng thời gian xử lý transaction.

## 2. Cơ Sở Lý Thuyết

Theo mô hình chi phí trong cơ sở dữ liệu phân tán của Özsu và Valduriez, chi phí xử lý một thao tác có thể được mô hình hóa như sau:

```text
Cost = IO + CPU + Comm
```

| Thành phần | Ý nghĩa trong đồ án |
|---|---|
| IO | Chi phí đọc/ghi dữ liệu trong SQLite |
| CPU | Chi phí xử lý logic transaction tại Coordinator và Participant Node |
| Comm | Chi phí truyền thông giữa Coordinator và Participant Node |

Trong thí nghiệm này, các yếu tố như dataset, số lượng node, database engine, transaction logic và cách đo metric được giữ cố định. Biến được thay đổi có kiểm soát là Network Latency.

Do đó, nếu tổng thời gian xử lý transaction tăng khi latency tăng, nguyên nhân chính có thể được giải thích là do thành phần `Comm` tăng.

Hệ thống sử dụng giao thức Two-Phase Commit gồm hai phase chính:

| Phase | Vai trò |
|---|---|
| PREPARE / VOTING | Coordinator hỏi các Participant Node có sẵn sàng commit hay không |
| COMMIT / ABORT | Coordinator gửi quyết định cuối cùng đến các Participant Node |

Vì 2PC cần ít nhất hai vòng giao tiếp giữa Coordinator và Participant Node, giao thức này chịu ảnh hưởng rõ rệt khi Network Latency tăng.

## 3. Phương Pháp Benchmark

Benchmark được thực hiện với ba mức Network Latency: `1ms`, `50ms`, `250ms`.

Với mỗi mức latency, hệ thống chạy:

```text
5 runs x 100 transactions = 500 transactions
```

Tổng số transaction được đo chính thức:

```text
3 latency levels x 500 transactions = 1500 transactions
```

Trước khi đo chính thức, hệ thống thực hiện warm-up để giảm ảnh hưởng của các yếu tố khởi động ban đầu.

Các metric được thu thập gồm:

| Metric | Ý nghĩa |
|---|---|
| `total_time_ms` | Tổng thời gian xử lý transaction |
| `prepare_phase_ms` | Thời gian thực hiện phase PREPARE |
| `decision_phase_ms` | Thời gian thực hiện phase COMMIT hoặc ABORT |
| `doing_work_ms` | Thời gian xử lý thực tại các node |
| `network_wait_ms` | Thời gian chờ mạng |
| `coordination_cost_percent` | Tỷ lệ chi phí điều phối |
| `mean_total_time_ms` | Thời gian trung bình |
| `median_total_time_ms` | Thời gian trung vị |
| `p99_total_time_ms` | Tail latency tại percentile 99 |
| `abort_rate_percent` | Tỷ lệ transaction thất bại |

Công thức tính Network Waiting Time:

```text
Network Waiting Time = Total Transaction Time - Doing Work Time
```

Công thức tính Cost of Coordination:

```text
Cost of Coordination (%) = Network Waiting Time / Total Transaction Time x 100
```

## 4. Kết Quả Benchmark

Kết quả benchmark tổng hợp từ `benchmark/results_summary.csv`:

| Latency | Transactions | Success | Abort Rate | Mean Total Time | Median Total Time | P99 Total Time | Mean Doing Work | Mean Network Waiting | Cost of Coordination |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1ms | 500 | 500 | 0.00% | 57.97 ms | 56.94 ms | 99.21 ms | 23.25 ms | 34.72 ms | 58.70% |
| 50ms | 500 | 500 | 0.00% | 253.30 ms | 250.62 ms | 288.27 ms | 24.38 ms | 228.92 ms | 90.37% |
| 250ms | 500 | 500 | 0.00% | 1057.85 ms | 1053.50 ms | 1115.83 ms | 28.33 ms | 1029.52 ms | 97.33% |

Kết quả cho thấy hệ thống xử lý thành công toàn bộ 1500 transaction trong điều kiện các node hoạt động bình thường. Abort Rate ở cả ba mức latency đều bằng 0%, cho thấy hệ thống ổn định trong quá trình benchmark.

## 5. Phân Tích Total Transaction Time

![Total Transaction Time by Latency](../analysis/charts/total_time_by_latency.png)

Mean Total Transaction Time tăng mạnh khi Network Latency tăng.

Ở mức latency 1ms, thời gian xử lý trung bình là 57.97 ms. Khi latency tăng lên 50ms, thời gian xử lý trung bình tăng lên 253.30 ms. Ở mức latency 250ms, thời gian xử lý trung bình đạt 1057.85 ms.

So với mức latency 1ms, thời gian xử lý trung bình ở mức 250ms tăng khoảng:

```text
1057.85 / 57.97 ~= 18.25 lần
```

Điều này chứng minh Network Latency có tác động trực tiếp đến hiệu năng của Distributed Transaction sử dụng Two-Phase Commit. Sự gia tăng này xuất hiện vì 2PC cần nhiều vòng giao tiếp giữa Coordinator và Participant Node. Khi latency tăng, thời gian truyền thông trong mỗi phase cũng tăng theo.

## 6. Phân Tích Cost of Coordination

![Cost of Coordination](../analysis/charts/coordination_cost.png)

Cost of Coordination tăng mạnh theo Network Latency.

Ở mức latency 1ms, Cost of Coordination chiếm 58.70% tổng thời gian xử lý. Khi latency tăng lên 50ms, tỷ lệ này đạt 90.37%. Ở mức 250ms, Cost of Coordination đạt 97.33%.

Điều này cho thấy trong môi trường mạng có độ trễ cao, phần lớn thời gian xử lý transaction không nằm ở thao tác đọc/ghi dữ liệu hoặc xử lý CPU, mà nằm ở chi phí truyền thông và điều phối giữa Coordinator với các Participant Node.

Kết quả này phù hợp với mô hình:

```text
Cost = IO + CPU + Comm
```

Trong đó `Comm` là thành phần tăng mạnh nhất khi Network Latency tăng.

## 7. Phân Tích Doing Work Time Và Network Waiting Time

![Doing Work vs Network Waiting](../analysis/charts/work_vs_network.png)

Biểu đồ Doing Work vs Network Waiting là biểu đồ quan trọng nhất vì nó tách tổng thời gian xử lý thành hai phần:

| Thành phần | Ý nghĩa |
|---|---|
| Doing Work Time | Thời gian xử lý thực tại node |
| Network Waiting Time | Thời gian chờ truyền thông và điều phối |

Doing Work Time gần như ổn định ở cả ba mức latency:

| Latency | Mean Doing Work |
|---:|---:|
| 1ms | 23.25 ms |
| 50ms | 24.38 ms |
| 250ms | 28.33 ms |

Trong khi đó, Network Waiting Time tăng rất mạnh:

| Latency | Mean Network Waiting |
|---:|---:|
| 1ms | 34.72 ms |
| 50ms | 228.92 ms |
| 250ms | 1029.52 ms |

Điều này chứng minh sự gia tăng tổng thời gian xử lý transaction chủ yếu đến từ thời gian chờ mạng, không phải do thời gian xử lý thực tại node.

Nói cách khác, khi latency tăng, thành phần IO và CPU gần như không thay đổi, còn thành phần Comm tăng mạnh. Đây là đặc trưng quan trọng của hệ cơ sở dữ liệu phân tán khi các node nằm xa nhau về mặt mạng.

## 8. Phân Tích Mean, Median Và P99

![Mean Median P99](../analysis/charts/mean_median_p99.png)

Biểu đồ Mean, Median và P99 cho thấy cả ba chỉ số đều tăng khi Network Latency tăng.

| Latency | Mean | Median | P99 |
|---:|---:|---:|---:|
| 1ms | 57.97 ms | 56.94 ms | 99.21 ms |
| 50ms | 253.30 ms | 250.62 ms | 288.27 ms |
| 250ms | 1057.85 ms | 1053.50 ms | 1115.83 ms |

Mean phản ánh thời gian xử lý trung bình. Median phản ánh thời gian xử lý điển hình của phần lớn transaction. P99 phản ánh tail latency, tức nhóm transaction chậm nhất trong hệ thống.

Việc Mean, Median và P99 cùng tăng cho thấy ảnh hưởng của Network Latency là nhất quán trên toàn bộ tập transaction, không chỉ xuất hiện ở một vài trường hợp bất thường.

P99 tăng lên 1115.83 ms ở mức latency 250ms cho thấy các transaction chậm nhất cũng chịu ảnh hưởng rất lớn từ độ trễ mạng.

## 9. Phân Tích Theo Phase Của Two-Phase Commit

Trong Two-Phase Commit, mỗi transaction cần hai phase giao tiếp chính:

| Phase | Ý nghĩa |
|---|---|
| PREPARE | Coordinator gửi yêu cầu chuẩn bị và chờ vote |
| COMMIT / ABORT | Coordinator gửi quyết định cuối cùng và chờ ACK |

Kết quả benchmark cho thấy thời gian của hai phase này tăng theo Network Latency:

| Latency | Prepare Phase | Decision Phase |
|---:|---:|---:|
| 1ms | 28.95 ms | 29.01 ms |
| 50ms | 126.39 ms | 126.90 ms |
| 250ms | 528.41 ms | 529.43 ms |

Hai phase có thời gian gần tương đương nhau vì cả hai đều yêu cầu Coordinator gửi request đến các Participant Node và chờ response. Khi latency tăng, cả hai phase đều bị ảnh hưởng.

Điều này phù hợp với bản chất của Two-Phase Commit: giao thức đảm bảo Atomicity cho Distributed Transaction nhưng phải trả giá bằng chi phí điều phối và truyền thông cao.

## 10. Failure Scenario

Ngoài benchmark trong điều kiện bình thường, hệ thống còn được kiểm tra với Failure Scenario bằng cách mô phỏng Node B bị crash.

Khi Node B bị crash, Coordinator không nhận đủ vote YES trong phase PREPARE. Theo quy tắc của Two-Phase Commit, Coordinator quyết định GLOBAL ABORT và gửi lệnh ABORT đến các node còn lại.

Kết quả log cho thấy transaction `TX_FAIL_NODE_B_001` có:

| Trường | Giá trị |
|---|---|
| Decision | ABORT |
| Status | FAILED |
| Failed node | Node B |

Kết quả này chứng minh hệ thống không xảy ra partial commit. Không có trường hợp một số node đã commit trong khi node khác bị lỗi và không commit.

Ý nghĩa của Failure Scenario là chứng minh Two-Phase Commit giúp đảm bảo tính Atomicity trong môi trường phân tán.

Tuy nhiên, 2PC vẫn có hạn chế. Nếu Coordinator bị lỗi sau khi Participant đã vote YES và đang chờ quyết định cuối cùng, hệ thống có thể rơi vào trạng thái blocking. Trong phạm vi đồ án này, hệ thống mới mô phỏng lỗi Participant Node, chưa mô phỏng lỗi Coordinator.

## 11. Kết Luận

Kết quả thực nghiệm cho thấy Network Latency có ảnh hưởng rất lớn đến Distributed Transaction sử dụng Two-Phase Commit.

Khi latency tăng từ 1ms lên 50ms và 250ms, Mean Total Transaction Time tăng từ 57.97 ms lên 253.30 ms và 1057.85 ms. Trong khi đó, Doing Work Time gần như ổn định, chỉ tăng nhẹ từ 23.25 ms lên 28.33 ms.

Network Waiting Time tăng mạnh từ 34.72 ms lên 228.92 ms và 1029.52 ms. Tương ứng, Cost of Coordination tăng từ 58.70% lên 90.37% và 97.33%.

Kết quả này chứng minh rằng trong Distributed Transaction, đặc biệt với giao thức Two-Phase Commit, Communication Cost có thể trở thành thành phần chi phối tổng thời gian xử lý khi các node nằm xa nhau về mặt mạng.

Kết quả thực nghiệm phù hợp với mô hình chi phí:

```text
Cost = IO + CPU + Comm
```

Trong đó IO và CPU gần như cố định, còn Comm tăng mạnh theo Network Latency.

Do đó, đối với các hệ thống phân tán trên phạm vi rộng như regional hoặc trans-atlantic deployment, cần cân nhắc chi phí truyền thông khi lựa chọn cơ chế commit, thiết kế phân mảnh dữ liệu và triển khai transaction.
