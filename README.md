# Sudoku SAT Solving

Khung mã nguồn cho bài tập lớn so sánh các phương pháp giải Sudoku. Đã có định dạng đề, bộ kiểm tra nghiệm, kiểu kết quả chung và SAT solver đầu tiên dùng sequential counter. Chưa cài đặt các solver khác, bộ dữ liệu benchmark hay kết quả thực nghiệm.

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
| `src/sudoku_bench/solvers/base.py` | Kiểu kết quả và trạng thái dùng chung cho các solver. |
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

- [x] Định nghĩa định dạng đầu vào/đầu ra chung và cài `puzzle.py`, `validator.py`.
- [x] Cài mô hình SAT và encoding AMO sequential counter.
- [ ] Cài CP Optimizer, CPLEX MIP, Gurobi MIP, CP-SAT.
- [ ] Thêm các encoding SAT còn lại để làm thí nghiệm mở rộng.
- [ ] Thu thập bộ đề, ghi nguồn và chia nhóm kích thước/độ khó.
- [ ] Chạy benchmark công bằng, lưu cả timeout và lỗi.
- [ ] Viết báo cáo và dẫn link repository ở mục Data Availability.

## Nguyên tắc thực nghiệm

Giữ cùng bộ đề, giới hạn thời gian và điều kiện máy cho mọi cấu hình. Tách thời gian xây mô hình khỏi thời gian giải. Kiểm tra mọi nghiệm bằng bộ xác thực độc lập. CPLEX MIP và Gurobi MIP phải dùng cùng công thức toán để so sánh bộ giải. Không coi timeout là vô nghiệm.

## Giao diện chung

Đề được lưu dạng JSON. `N` là số chính phương (`4`, `9`, `16`, `25`, ...); bảng có `N` hàng, mỗi hàng `N` ô. Số `0` biểu thị ô trống. Các số gợi ý phải thuộc `1…N` và không được trùng nhau trong cùng hàng, cột hoặc khối.

```json
{
  "id": "example-4x4",
  "grid": [
    [1, 0, 0, 4],
    [0, 4, 1, 0],
    [0, 1, 4, 0],
    [4, 0, 0, 1]
  ]
}
```

`load_puzzle(path)` đọc và kiểm tra đề. `Puzzle.from_rows(rows)` tạo đề trực tiếp. `validate_solution(puzzle, solution)` trả `True` khi nghiệm đầy đủ, đúng gợi ý, và mỗi hàng/cột/khối chứa đúng `1…N`; nếu không trả `False`.

Mỗi solver sau này trả một `SolveResult` gồm `status`, `solution`, `build_time_s`, `solve_time_s` và `message` tùy chọn. `status` thuộc `SOLVED`, `UNSAT`, `TIMEOUT`, `ERROR`. Chỉ `SOLVED` có nghiệm; thời gian tính bằng giây, không âm. `UNSAT` chỉ dùng khi solver chứng minh vô nghiệm; hết hạn chạy phải là `TIMEOUT`.

Chạy kiểm thử cơ bản:

```powershell
.\.venv\Scripts\Activate.ps1
python -m unittest discover -s tests -v
```

## Chạy SAT trên một đề

Cài gói trong môi trường ảo bằng Python 3.11 trở lên:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Giải đề 9×9 minh họa:

```powershell
python -m sudoku_bench.solvers.pysat_solver data/9x9/example.json
```

Lệnh in trạng thái, thời gian tạo mô hình, thời gian giải và bảng nghiệm nếu có. Mô hình dùng biến `x[r,c,d]` cho việc ô `(r,c)` nhận chữ số `d`; ràng buộc đúng một áp dụng cho ô, chữ số trong hàng, cột và khối. Mỗi ràng buộc gồm một mệnh đề ít nhất một và encoding sequential counter cho nhiều nhất một. Tệp `data/9x9/example.json` chỉ là đề minh họa, chưa thuộc bộ benchmark.
