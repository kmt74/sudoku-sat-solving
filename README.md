# Sudoku SAT Solving

Khung mã nguồn cho bài tập lớn so sánh các phương pháp giải Sudoku. Repository này mới có **cấu trúc và TODO**; chưa cài đặt solver, chưa có bộ dữ liệu benchmark và chưa có kết quả thực nghiệm.

## Phạm vi

- Bài toán: tìm một nghiệm Sudoku hợp lệ hoặc xác định vô nghiệm.
- Năm cấu hình chính: SAT/PySAT, IBM CP Optimizer, IBM CPLEX MIP, Gurobi MIP và OR-Tools CP-SAT.
- Phân tích mở rộng: bốn encoding SAT `binary`, `commander`, `product`, `sequential` được đề khuyến khích. Các encoding này không phải bốn họ phương pháp riêng.
- Mọi cấu hình phải chạy trên cùng bộ đề và được kiểm tra nghiệm bằng `validator.py`.

## Sơ đồ mã nguồn

| Thành phần | Vai trò |
|---|---|
| `src/sudoku_bench/puzzle.py` | Đọc, lưu và kiểm tra định dạng đề Sudoku. |
| `src/sudoku_bench/validator.py` | Kiểm tra nghiệm độc lập với solver. |
| `src/sudoku_bench/models/` | Xây mô hình toán/SAT cho từng họ phương pháp. |
| `src/sudoku_bench/encodings/` | Các cách mã hóa ràng buộc AMO cho SAT. |
| `src/sudoku_bench/solvers/` | Gọi từng bộ giải và chuyển kết quả về định dạng chung. |
| `src/sudoku_bench/benchmark.py` | Chạy cùng bộ đề, đo thời gian, ghi kết quả gốc. |
| `data/` | Bộ đề 9×9, 16×16 và 25×25 (nếu khả thi). |
| `tests/` | Kiểm thử tính đúng của dữ liệu, encoding và nghiệm. |
| `results/` | Kết quả gốc, bảng tổng hợp và biểu đồ. |
| `scripts/` | Lệnh chạy toàn bộ và tổng hợp kết quả. |
| `report/` | Mã nguồn báo cáo dạng bài báo khoa học. |

## TODO theo thứ tự

- [ ] Định nghĩa định dạng đầu vào/đầu ra chung và cài `puzzle.py`, `validator.py`.
- [ ] Cài mô hình SAT và một encoding AMO chạy đúng.
- [ ] Cài CP Optimizer, CPLEX MIP, Gurobi MIP, CP-SAT.
- [ ] Thêm các encoding SAT còn lại để làm thí nghiệm mở rộng.
- [ ] Thu thập bộ đề, ghi nguồn và chia nhóm kích thước/độ khó.
- [ ] Chạy benchmark công bằng, lưu cả timeout và lỗi.
- [ ] Viết báo cáo và dẫn link repository ở mục Data Availability.

## Nguyên tắc thực nghiệm

Giữ cùng bộ đề, giới hạn thời gian và điều kiện máy cho mọi cấu hình. Tách thời gian xây mô hình khỏi thời gian giải. Kiểm tra mọi nghiệm bằng bộ xác thực độc lập. CPLEX MIP và Gurobi MIP phải dùng cùng công thức toán để so sánh bộ giải. Không coi timeout là vô nghiệm.
