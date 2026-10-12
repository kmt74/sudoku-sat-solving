# Sudoku SAT Solving

Mã nguồn cho bài tập so sánh các phương pháp giải chính xác Sudoku: SAT, CP, MIP và CP-SAT. Chương trình nhận bảng `N×N` với `N` là số chính phương, dùng `0` cho ô trống, và kiểm tra độc lập mọi nghiệm trước khi ghi kết quả.

## Các cấu hình đã cài

| Tên chạy | Mô hình | Bộ giải |
|---|---|---|
| `sat-binary` | CNF, AMO binary/bitwise | PySAT Glucose3 |
| `sat-commander` | CNF, AMO commander | PySAT Glucose3 |
| `sat-product` | CNF, AMO 2-product | PySAT Glucose3 |
| `sat-sequential` | CNF, AMO sequential counter | PySAT Glucose3 |
| `cp-optimizer` | Biến nguyên và `all_diff` | IBM CP Optimizer |
| `cplex-mip` | Biến nhị phân `x[r,c,d]` | IBM CPLEX MIP |
| `gurobi-mip` | Cùng công thức MIP với CPLEX | Gurobi |
| `cp-sat` | Biến nguyên và `AddAllDifferent` | OR-Tools CP-SAT |

Với SAT, mỗi ràng buộc “đúng một” gồm một mệnh đề ALO và một encoding AMO. Có bốn nhóm ràng buộc: ô, chữ số trong hàng, chữ số trong cột và chữ số trong khối. Hai MIP cùng dùng các nhóm biến/ràng buộc từ `models/mip.py`.

## Cài đặt trên Windows

Từ thư mục gốc repo, dùng Python 3.11 trở lên:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[all]"
.\.venv\Scripts\python.exe scripts/check_setup.py
```

Nếu chỉ muốn chạy SAT và CP-SAT, có thể cài `-e ".[ortools]"`. Package SAT (`python-sat`) là phụ thuộc mặc định. Các gói `docplex`, `cplex` và `gurobipy` được cài bằng extra `all`; **cài package không đồng nghĩa đã có license đầy đủ**.

### CP Optimizer và license thương mại

`docplex.cp` cần chương trình `cpoptimizer.exe` từ IBM ILOG CPLEX Optimization Studio. Chỉ cài `docplex`/`cplex` bằng pip không cung cấp chương trình này. Sau khi cài Optimization Studio, đặt biến môi trường trong PowerShell (thay bằng đường dẫn thật):

```powershell
$env:CP_OPTIMIZER_EXECUTABLE = "<đường dẫn đầy đủ tới cpoptimizer.exe>"
.\.venv\Scripts\python.exe scripts/check_setup.py
```

Trên Windows, `cpoptimizer.exe` có thể không khởi động được nếu thiếu thư mục DLL của IBM trong `PATH` (lỗi `Nothing to read from local solver process`). Khi đó, thêm cả hai thư mục `cpoptimizer\bin\x64_win64` và `cplex\bin\x64_win64` của bản cài trước khi chạy. Ví dụ nếu cài Studio tại `D:\Applications`:

```powershell
$studio = 'D:\Applications'
$env:CP_OPTIMIZER_EXECUTABLE = Join-Path $studio 'cpoptimizer\bin\x64_win64\cpoptimizer.exe'
$env:PATH = (Join-Path $studio 'cpoptimizer\bin\x64_win64') + ';' + (Join-Path $studio 'cplex\bin\x64_win64') + ';' + $env:PATH
.\.venv\Scripts\python.exe scripts/check_setup.py
```

Đường dẫn trong ví dụ phải đổi theo nơi bạn cài IBM. Sau khi chỉnh biến môi trường người dùng trên Windows, mở lại PowerShell/IDE để cửa sổ mới nhận cấu hình.

CPLEX và Gurobi ở license giới hạn có thể giải 9×9 nhưng báo `ERROR` cho MIP 16×16/25×25 vì mô hình vượt giới hạn kích thước. Cần license học thuật/đầy đủ của hãng để thực nghiệm MIP kích thước lớn. Mã ghi đúng thông báo lỗi vào kết quả, không đổi lỗi license thành `TIMEOUT` hay `UNSAT`. Xem [DOcplex/CP Optimizer setup](https://ibmdecisionoptimization.github.io/docplex-doc/getting_started.html) và [Gurobi licensing](https://www.gurobi.com/academia/academic-program-and-licenses/).

## Chạy thử

Giải một đề 9×9 bằng SAT:

```powershell
.\.venv\Scripts\python.exe -m sudoku_bench.solvers.pysat_solver data/9x9/example.json --encoding sequential --time-limit 30
```

Chạy cả tám cấu hình trên đề 9×9 (mặc định mỗi lần giải tối đa 30 giây):

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py --data data/9x9 --repeats 3 --time-limit 30
```

Chạy nhóm có thể hoạt động trên 16×16/25×25 mà không cần license MIP lớn:

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py --data data/16x16 --methods sat-binary sat-commander sat-product sat-sequential cp-sat --time-limit 30
.\.venv\Scripts\python.exe scripts/run_all.py --data data/25x25 --methods sat-binary sat-commander sat-product sat-sequential cp-sat --time-limit 30
```

`--data` nhận một file JSON hoặc một thư mục (đọc đệ quy). `--methods` chọn cấu hình, `--seed` cố định thứ tự ngẫu nhiên của các phương pháp, `--output` chọn file kết quả. Mỗi solver dùng một luồng xử lý; giới hạn thời gian áp dụng cho **pha giải**, còn thời gian tạo mô hình được đo riêng.

Kết quả gốc là JSONL trong `results/raw/`: dòng đầu ghi môi trường/phụ thuộc, các dòng sau ghi từng lượt chạy, trạng thái, thời gian, số biến/ràng buộc và nghiệm. Để có bảng CSV sơ bộ:

```powershell
.\.venv\Scripts\python.exe scripts/summarize.py results/raw/<tên-file>.jsonl
```

Chỉ các lượt `SOLVED` có nghiệm hợp lệ được tính trong trung vị thời gian. `UNSAT`, `TIMEOUT` và `ERROR` được đếm riêng.

## Dữ liệu và kiểm thử

Định dạng đề:

```json
{
  "id": "example-4x4",
  "grid": [[1, 0, 0, 4], [0, 4, 1, 0], [0, 1, 4, 0], [4, 0, 0, 1]]
}
```

`puzzle.py` từ chối đề sai kích thước, giá trị hoặc mâu thuẫn giữa các ô gợi ý. `validator.py` kiểm tra bảng nghiệm không phụ thuộc solver. `data/9x9/example.json` và các file `smoke-seed0.json` 16×16/25×25 là **đề thử đường chạy**, chưa phải bộ benchmark cân bằng theo độ khó. Tạo lại đề smoke bằng:

Mỗi JSON có thể thêm `source`, `difficulty`, `kind`; benchmark chép các trường này vào kết quả gốc để bạn lọc và trích dẫn bộ đề khi viết báo cáo.

```powershell
.\.venv\Scripts\python.exe scripts/generate_smoke.py --sizes 16 25 --blanks-per-row 2 --seed 0
```

Khi làm báo cáo, hãy bổ sung bộ đề có nguồn, nhóm kích thước/độ khó và chính sách chọn mẫu rõ ràng. Đừng dùng thời gian trên đề gần hoàn chỉnh này để kết luận phương pháp nào nhanh hơn nói chung.

Chạy kiểm thử:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Cấu trúc

- `src/sudoku_bench/puzzle.py`, `validator.py`: định dạng đề và kiểm nghiệm.
- `src/sudoku_bench/encodings/`: bốn AMO encoding.
- `src/sudoku_bench/models/`: công thức SAT, CP, MIP, CP-SAT.
- `src/sudoku_bench/solvers/`: adapter trả chung `SolveResult`.
- `src/sudoku_bench/benchmark.py`: chạy cùng bộ đề, giới hạn thời gian, kiểm tra nghiệm, ghi kết quả.
- `scripts/`: lệnh kiểm tra setup, tạo đề smoke, chạy benchmark, tổng hợp CSV.
- `report/`: khung báo cáo để hoàn thiện sau.

`SolveResult.status` thuộc `SOLVED`, `UNSAT`, `TIMEOUT`, `ERROR`. `UNSAT` chỉ dùng khi solver chứng minh vô nghiệm. Trường hợp tìm được nghiệm hợp lệ ngay trước giới hạn thời gian vẫn là `SOLVED`; trường hợp thiếu phần mềm/license là `ERROR`.
