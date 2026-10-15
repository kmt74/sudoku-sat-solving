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

`docplex.cp` cần chương trình `cpoptimizer.exe` từ IBM ILOG CPLEX Optimization Studio. Chỉ cài `docplex`/`cplex` bằng pip không cung cấp chương trình này. Sau khi cài Optimization Studio, đặt biến môi trường trong PowerShell (thay bằng đường dẫn cài thực tế):

```powershell
$studio = 'C:\Program Files\IBM\ILOG\CPLEX_Studio222'
$env:CP_OPTIMIZER_EXECUTABLE = Join-Path $studio 'cpoptimizer\bin\x64_win64\cpoptimizer.exe'
$env:PATH = (Join-Path $studio 'cpoptimizer\bin\x64_win64') + ';' + (Join-Path $studio 'cplex\bin\x64_win64') + ';' + $env:PATH
.\.venv\Scripts\python.exe scripts/check_setup.py
```

Nếu đã cài **bản Academic hoặc bản đầy đủ**, nâng runtime CPLEX bên trong `.venv` để giải mô hình MIP lớn hơn giới hạn Community:

```powershell
.\.venv\Scripts\python.exe -m pip install setuptools
.\.venv\Scripts\docplex.exe config --upgrade $studio
```

Trên Windows, `cpoptimizer.exe` có thể không khởi động được nếu thiếu thư mục DLL của IBM trong `PATH` (lỗi `Nothing to read from local solver process`). Khi chỉnh biến môi trường người dùng, mở lại PowerShell/IDE để cửa sổ mới nhận cấu hình. Nếu tạo lại `.venv`, hãy chạy lại lệnh `docplex config --upgrade`.

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

Để đo RAM đỉnh, thêm `--measure-memory`. Mỗi lượt chạy trong một tiến trình Python
riêng; chương trình cố gắng lấy mẫu RSS của tiến trình đó cùng các tiến trình
con (gồm `cpoptimizer.exe`) mỗi 10 ms:

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py --data data/benchmark/9x9/easy --repeats 3 --time-limit 30 --measure-memory
```

Chạy nhóm có thể hoạt động trên 16×16/25×25 mà không cần license MIP lớn:

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py --data data/16x16 --methods sat-binary sat-commander sat-product sat-sequential cp-sat --time-limit 30
.\.venv\Scripts\python.exe scripts/run_all.py --data data/25x25 --methods sat-binary sat-commander sat-product sat-sequential cp-sat --time-limit 30
```

`--data` nhận một file JSON hoặc một thư mục (đọc đệ quy). `--methods` chọn cấu hình, `--seed` cố định thứ tự ngẫu nhiên của các phương pháp, `--output` chọn file kết quả. Mỗi solver dùng một luồng xử lý; giới hạn thời gian áp dụng cho **pha giải**, còn thời gian tạo mô hình được đo riêng.

Các cột thời gian trong từng dòng kết quả:

| Cột | Ý nghĩa |
| --- | --- |
| `build_time_s` | Thời gian solver tạo mô hình hoặc mã hóa SAT. |
| `solve_time_s` | Thời gian gọi bộ giải và lấy nghiệm. |
| `total_time_s` | Tổng hai thời gian trên; dùng để so sánh hiệu năng thuật toán. |
| `attempt_wall_s` | Thời gian thực cả lượt, gồm nạp thư viện/khởi động tiến trình khi bật đo RAM, kiểm tra nghiệm và các phần phụ trợ. |
| `peak_rss_bytes` | RAM resident lớn nhất quan sát được của cây tiến trình; `null` khi không bật đo RAM. Chia cho 1.048.576 để đổi sang MiB. |
| `peak_child_rss_bytes` | RAM resident lớn nhất quan sát được riêng ở các tiến trình con; giúp kiểm tra phần bộ nhớ của CP Optimizer. |
| `memory_samples` | Số mẫu RAM thu được trong lượt chạy. |

RSS được lấy mẫu nên một đỉnh rất ngắn có thể bị bỏ lỡ. Tổng RSS của tiến trình
cha và con cũng có thể tính trùng các trang bộ nhớ chia sẻ. Dùng cùng chế độ
`--measure-memory` cho toàn bộ lượt cần so sánh; đọc `measurement_mode` và
`memory_sample_interval_s` ở dòng metadata đầu tiên. Thời gian thực khi bật đo
RAM bao gồm chi phí khởi động Python nên không thay cho `total_time_s`.

Kết quả gốc là JSONL trong `results/raw/`: dòng đầu ghi môi trường/phụ thuộc, các dòng sau ghi từng lượt chạy, trạng thái, thời gian, số biến/ràng buộc và nghiệm. Để có bảng CSV sơ bộ:

```powershell
.\.venv\Scripts\python.exe scripts/summarize.py results/raw/<tên-file>.jsonl
```

Chỉ các lượt `SOLVED` có nghiệm hợp lệ được tính trong trung vị thời gian.
Trung vị và cực đại RAM dùng các lượt không có trạng thái `ERROR` và có mẫu RAM;
CSV ghi theo MiB. `UNSAT`, `TIMEOUT` và `ERROR` được đếm riêng.

## Dữ liệu và kiểm thử

Định dạng đề:

```json
{
  "id": "example-4x4",
  "grid": [[1, 0, 0, 4], [0, 4, 1, 0], [0, 1, 4, 0], [4, 0, 0, 1]]
}
```

`puzzle.py` từ chối đề sai kích thước, giá trị hoặc mâu thuẫn giữa các ô gợi ý. `validator.py` kiểm tra bảng nghiệm không phụ thuộc solver. Bộ 90 đề cân bằng theo kích thước và nhóm độ khó nằm tại [data/benchmark/README.md](data/benchmark/README.md); `manifest.csv` giữ nhãn gốc và đường dẫn nguồn của từng đề. Chạy bộ này bằng `--data data/benchmark`. `data/9x9/example.json` và các file `smoke-seed0.json` 16×16/25×25 chỉ là **đề thử đường chạy**. Tạo lại đề smoke bằng:

```powershell
.\.venv\Scripts\python.exe scripts/generate_smoke.py --sizes 16 25 --blanks-per-row 2 --seed 0
```

Mỗi JSON có thể thêm `source`, `difficulty`, `hardness_level`, `kind`; benchmark chép các trường này vào kết quả gốc để bạn lọc và trích dẫn bộ đề khi viết báo cáo.

Khi làm báo cáo, trình bày quy tắc gộp nhãn suy diễn ràng buộc gốc thành ba nhóm độ khó. Đừng dùng thời gian trên đề smoke gần hoàn chỉnh để kết luận phương pháp nào nhanh hơn nói chung.

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
