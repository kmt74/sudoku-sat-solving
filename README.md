# Sudoku SAT Solving

Thực nghiệm so sánh các cách mô hình hóa và giải Sudoku tổng quát bằng **SAT, ILP/MIP, CP và CP-SAT**. Trọng tâm là bốn cách mã hóa ràng buộc nhiều nhất một trong SAT, sau đó đối chiếu với các bộ giải khác trên cùng bộ đề, hạn thời gian và quy trình kiểm tra nghiệm.

Đầu vào là bảng `N × N`, với `N = b²`, khối `b × b` và `0` biểu thị ô trống. Mọi nghiệm được kiểm tra độc lập theo hàng, cột, khối và ô gợi ý trước khi được công nhận là hợp lệ.

## 1. Mục tiêu

1. **So sánh bốn SAT encoding:** kích thước công thức, thời gian dựng/giải, tỷ lệ hoàn tất và bộ nhớ khi cùng dùng Glucose3.
2. **So sánh SAT trung bình:** trung bình hiệu năng bốn cấu hình SAT với CP Optimizer, CPLEX MIP, Gurobi MIP và CP-SAT.
3. **So sánh một SAT encoding cố định:** chọn một encoding theo tiêu chí toàn mẫu, rồi xét lợi thế theo kích thước, độ khó và bộ nhớ.

SAT trung bình là thống kê tổng hợp, không phải bộ giải mới. Encoding tốt nhất phải được giữ cố định khi đối chiếu, không chọn lại cấu hình nhanh nhất riêng cho từng đề. Chọn và đánh giá trên cùng dữ liệu chỉ cho kết luận mô tả bộ mẫu đó.

## 2. Tám cấu hình

| Tên dòng lệnh | Mô hình | Bộ giải |
| --- | --- | --- |
| `sat-binary` | CNF, AMO Binary/bitwise | Glucose3 qua PySAT |
| `sat-commander` | CNF, AMO Commander, nhóm tối đa 3 | Glucose3 qua PySAT |
| `sat-product` | CNF, AMO 2-Product | Glucose3 qua PySAT |
| `sat-sequential` | CNF, AMO Sequential của Sinz | Glucose3 qua PySAT |
| `cplex-mip` | Biến nhị phân ô–số, các tổng bằng 1 | IBM CPLEX |
| `gurobi-mip` | Cùng mô hình nhị phân với CPLEX | Gurobi |
| `cp-optimizer` | Biến nguyên cho từng ô, `all_diff` | IBM CP Optimizer qua DOcplex |
| `cp-sat` | Biến ô và `AddAllDifferent` | OR-Tools CP-SAT |

**Thuật ngữ:** SAT là tính khả thỏa logic Boolean; CNF là hội của các mệnh đề tuyển; ALO (at-least-one) yêu cầu ít nhất một lựa chọn đúng; AMO (at-most-one) yêu cầu nhiều nhất một. ALO kết hợp AMO tạo điều kiện đúng một. ILP là quy hoạch tuyến tính nguyên; MIP là quy hoạch hỗn hợp nguyên, bao gồm ILP như một trường hợp riêng. CP là lập trình ràng buộc; `all_diff`/`AddAllDifferent` yêu cầu các biến nhận giá trị đôi một khác nhau.

SAT giữ bốn họ nhóm đúng một: ô–số, hàng–số, cột–số và khối–số. Các cấu hình chỉ thay cách mã hóa AMO. Hai bộ giải MIP dùng chung công thức trong [`models/mip.py`](src/sudoku_bench/models/mip.py).

## 3. Cài đặt

### Python và thư viện

Yêu cầu **Python 3.11 trở lên**. Ví dụ dưới dùng Python 3.12 và PowerShell. Mọi lệnh chạy từ thư mục gốc repo; gọi trực tiếp Python trong môi trường ảo nên không cần kích hoạt môi trường.

```powershell
git clone https://github.com/kmt74/sudoku-sat-solving.git
cd sudoku-sat-solving
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[all]"
```

Nếu chỉ chạy SAT và CP-SAT:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[ortools]"
```

SAT (`python-sat`) và công cụ đo bộ nhớ (`psutil`) là phụ thuộc mặc định. Các nhóm cài thêm gồm `ortools`, `ibm`, `gurobi`, `all`; xem [`pyproject.toml`](pyproject.toml). Trên Linux/macOS, dùng `python3 -m venv .venv` và thay đường dẫn Python bằng `.venv/bin/python`.

### IBM CPLEX và CP Optimizer

`docplex` là thư viện mô hình hóa. **CP Optimizer còn cần chương trình thực thi** từ IBM ILOG CPLEX Optimization Studio. Sau khi cài, thay đường dẫn dưới đây theo bản cài thực tế:

```powershell
$studio = 'C:\Program Files\IBM\ILOG\CPLEX_Studio222'
$env:CP_OPTIMIZER_EXECUTABLE = Join-Path $studio 'cpoptimizer\bin\x64_win64\cpoptimizer.exe'
$env:PATH = (Join-Path $studio 'cpoptimizer\bin\x64_win64') + ';' + (Join-Path $studio 'cplex\bin\x64_win64') + ';' + $env:PATH
```

Với bản Academic/đầy đủ, cấu hình runtime CPLEX tương ứng trong môi trường Python:

```powershell
.\.venv\Scripts\python.exe -m pip install setuptools
.\.venv\Scripts\docplex.exe config --upgrade $studio
```

Lệnh cần bản Optimization Studio đã cài và phiên bản Python được bản đó hỗ trợ. Thiếu DLL trong `PATH` có thể khiến CP Optimizer không khởi động được. Nếu đặt biến môi trường người dùng, mở lại terminal/IDE; nếu tạo lại `.venv`, cấu hình lại runtime.

### Gurobi và giấy phép

`gurobipy` được cài qua nhóm `gurobi` hoặc `all`; thiết lập giấy phép theo hướng dẫn của hãng. **Cài gói Python không đồng nghĩa có giấy phép cho mô hình lớn.** CPLEX/Gurobi bản giới hạn có thể chạy đề nhỏ nhưng từ chối mô hình `16 × 16` hoặc `25 × 25`. Kiểm tra giấy phép trên kích thước dự định chạy; phép thử `4 × 4` chỉ xác nhận đường gọi cơ bản.

Hướng dẫn chính thức: [IBM DOcplex](https://ibmdecisionoptimization.github.io/docplex-doc/getting_started.html), [Gurobi Academic](https://www.gurobi.com/academia/academic-program-and-licenses/).

### Kiểm tra môi trường

```powershell
.\.venv\Scripts\python.exe scripts/check_setup.py
```

Lệnh in phiên bản gói, vị trí CP Optimizer và trạng thái tám cấu hình trên đề `4 × 4`. Đọc kết quả từng cấu hình và thông báo lỗi; mã thoát của tiện ích không thay thế việc kiểm tra từng trạng thái.

## 4. Chạy thử và thực nghiệm

### Giải một đề bằng SAT

```powershell
.\.venv\Scripts\python.exe -m sudoku_bench.solvers.pysat_solver data/9x9/example.json --encoding product --time-limit 60
```

Thay `product` bằng `binary`, `commander` hoặc `sequential` để đổi mã hóa.

### Chạy một nhóm đề và đo bộ nhớ

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py --data data/benchmark/9x9/easy --repeats 1 --time-limit 60 --measure-memory --output results/raw/trial-9x9-easy.jsonl
```

Nếu chưa cài IBM/Gurobi, chọn năm cấu hình không cần giấy phép thương mại:

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py --data data/benchmark/9x9/easy --methods sat-binary sat-commander sat-product sat-sequential cp-sat --repeats 1 --time-limit 60 --measure-memory --output results/raw/trial-open-solvers.jsonl
```

### Chạy đủ 90 đề

Sau khi kiểm tra môi trường cho mọi bộ giải cần dùng:

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py --data data/benchmark --repeats 3 --time-limit 60 --measure-memory --output results/raw/full-60s.jsonl
```

Đủ tám cấu hình tạo **90 × 8 × 3 = 2.160 lượt**. Các lượt chạy tuần tự; thứ tự cấu hình được xáo trộn trong mỗi lần lặp.

| Tham số | Ý nghĩa |
| --- | --- |
| `--data` | File JSON hoặc thư mục đề; đọc đệ quy. |
| `--methods` | Danh sách tên cấu hình ở mục 2. |
| `--repeats` | Số lần chạy mỗi cấu hình trên mỗi đề. |
| `--time-limit` | Hạn **pha giải**, tính bằng giây; các ví dụ đặt rõ 60. |
| `--seed` | Hạt giống xáo trộn thứ tự cấu hình; không đổi seed nội bộ từng bộ giải. |
| `--measure-memory` | Chạy mỗi lượt trong tiến trình riêng và lấy mẫu RSS của cây tiến trình. |
| `--output` | Tệp JSONL; nếu bỏ qua, tạo tên theo thời điểm trong `results/raw/`. |

`run_all.py` ghi mới tệp đầu ra; dùng tên khác cho thí nghiệm mới nếu cần giữ kết quả cũ. Hạn giải không phải hạn cứng cho cả tiến trình: dựng mô hình, khởi động, giao tiếp và dọn tài nguyên có thể làm thời gian thực vượt 60 giây.

## 5. Bộ đề và nguồn dữ liệu

[`data/benchmark/`](data/benchmark/README.md) chứa **90 đề**: ba kích thước `9 × 9`, `16 × 16`, `25 × 25`; mỗi kích thước có ba nhóm, mỗi nhóm 10 đề.

| Nhóm thực nghiệm | Nhãn suy luận gốc |
| --- | --- |
| `easy` | `Val`, `ValBS`, `ValDS`, `ValChan` |
| `medium` | `Bnd`, `BndBS`, `BndDS`, `BndChan` |
| `hard` | `Dom`, `DomBS`, `DomDS`, `UNSOLVED` |

Nguồn: [Scaled Sudoku Instances](https://github.com/zayenz/scaled-sudoku-instances), commit `a8596ccaa29587c821c1ccf29225a66a7b4d5a13`. Giấy phép dữ liệu: [MIT của nguồn](data/benchmark/LICENSE.upstream). [`manifest.csv`](data/benchmark/manifest.csv) giữ mã đề, nhãn gốc, kích thước, số gợi ý, đường dẫn nguồn và mã băm.

`Val`, `Bnd`, `Dom` lần lượt là lan truyền giá trị, cận và miền. `BS`/`DS` thử gán ở cận/trên toàn miền để loại giá trị gây mâu thuẫn; `Chan` liên kết nhiều biểu diễn. `UNSOLVED` nghĩa là các cấu hình suy luận đã thử chưa giải hết khi không tìm kiếm, **không có nghĩa đề vô nghiệm**. Ba nhóm là quy ước chọn mẫu, không phải thang độ khó cho người chơi hoặc bảo đảm thứ tự thời gian cho mọi bộ giải.

90 đề có 90 gốc nguồn khác nhau và giữ đủ 12 nhãn gốc. Xem README dữ liệu để biết quy trình chọn mẫu. Tính duy nhất dựa trên thông tin nguồn; dự án kiểm tra nghiệm tìm được, không chứng minh lại tính duy nhất trong mỗi lượt đo.

Các đề `example.json`/`smoke-seed0.json` ngoài thư mục benchmark chỉ để thử đường chạy. **Dùng `--data data/benchmark`, không dùng `--data data`, cho lượt so sánh chính.**

### Định dạng đề JSON

```json
{
  "id": "example-4x4",
  "grid": [[1, 0, 0, 4], [0, 4, 1, 0], [0, 1, 4, 0], [4, 0, 0, 1]]
}
```

Các trường tùy chọn `source`, `difficulty`, `hardness_level`, `kind` được giữ trong kết quả. Đầu vào bị từ chối khi sai kích thước, giá trị hoặc gợi ý mâu thuẫn.

## 6. Kết quả và cách đọc số đo

JSONL (JSON Lines) chứa một đối tượng JSON trên mỗi dòng: dòng đầu `kind: meta` lưu môi trường và thiết lập; các dòng `kind: result` lưu từng lượt, trạng thái, nghiệm và số đo.

| Trạng thái | Ý nghĩa |
| --- | --- |
| `SOLVED` | Đã tìm và kiểm tra nghiệm hợp lệ. |
| `UNSAT` | Bộ giải đã chứng minh đề vô nghiệm. |
| `TIMEOUT` | Quá hạn khi chưa có nghiệm. |
| `ERROR` | Lỗi phần mềm, môi trường, giấy phép hoặc nghiệm không hợp lệ; đọc `message`. |

| Trường | Ý nghĩa |
| --- | --- |
| `build_time_s` | Dựng/nạp mô hình; ranh giới phụ thuộc hàm giao tiếp bộ giải. |
| `solve_time_s` | Gọi giải và xử lý nghiệm theo từng hàm giao tiếp. |
| `total_time_s` | `build_time_s + solve_time_s`. |
| `attempt_wall_s` | Thời gian thực cả lượt, gồm các chi phí tiến trình và kiểm tra liên quan. |
| `peak_rss_bytes` | Tổng RSS lớn nhất quan sát được tại cùng thời điểm trên cây tiến trình. |
| `peak_child_rss_bytes` | Đỉnh RSS quan sát được riêng cho các tiến trình con. |
| `memory_samples` | Số lần lấy mẫu bộ nhớ. |
| `model_variables`, `model_constraints` | Số biến/ràng buộc khai báo; SAT đếm biến và clause. |
| `solution_valid`, `solution`, `message` | Kiểm tra nghiệm, bảng nghiệm và thông báo chẩn đoán. |

RSS (resident set size) là bộ nhớ tiến trình đang thường trú trong RAM. Chia byte cho `1.048.576` để đổi sang MiB. Chế độ đo RAM lấy mẫu khoảng 10 ms, gồm Python và tiến trình con như CP Optimizer; có thể bỏ sót đỉnh ngắn và đếm lặp trang chia sẻ. Đây là chi phí triển khai quan sát được, không phải độ phức tạp không gian lý thuyết. Khi không bật đo RAM, trường đỉnh bộ nhớ có thể là `null`.

Giữ cùng chế độ đo cho các cấu hình cần so sánh. `total_time_s` mô tả hai pha dựng và giải; `attempt_wall_s` phù hợp hơn khi lập kế hoạch chạy hoặc đánh giá ứng dụng khởi động tiến trình mới cho mỗi đề.

### Tổng hợp CSV

```powershell
.\.venv\Scripts\python.exe scripts/summarize.py results/raw/full-60s.jsonl --output results/summary/full-60s.csv
```

CSV tổng hợp theo kích thước và cấu hình, đếm riêng các trạng thái và tính trung vị thời gian trên lượt `SOLVED` có nghiệm hợp lệ. RSS tổng hợp trên lượt không lỗi và có số đo. Đọc trung vị cùng số lượt giải được: một cấu hình bỏ lại các đề khó có thể có trung vị thành công thấp.

**PAR2 cho báo cáo:** timeout nhận điểm `2 × hạn giải`; lượt thành công dùng thời gian giải thực đo. PAR2-total cộng thời gian dựng từng lượt trước khi lấy trung bình. Điểm phạt không phải thời gian ước lượng để giải xong đề timeout. `summarize.py` hiện xuất số đếm và trung vị; **không tự tính PAR2 hoặc SAT trung bình**. Các chỉ số này cần tái tính từ JSONL với hạn giải, trọng số nhóm và chính sách xử lý lỗi được công bố.

## 7. Cấu trúc

```text
src/sudoku_bench/
  puzzle.py               # Đọc đề, kiểm tra cấu trúc và gợi ý
  validator.py            # Kiểm tra nghiệm độc lập
  encodings/              # Bốn mã hóa AMO
  models/                 # Công thức SAT, ILP, CP và CP-SAT
  solvers/                # Giao tiếp bộ giải, chung hợp đồng SolveResult
  benchmark.py            # Điều phối, kiểm nghiệm và ghi JSONL
  isolated_run.py         # Tiến trình riêng và lấy mẫu RSS
  benchmark_worker.py     # Thực hiện một lượt trong tiến trình con
scripts/                  # Kiểm tra cài đặt, chạy đề, tổng hợp CSV
data/benchmark/           # 90 đề, danh mục nguồn và giấy phép
tests/                    # Kiểm thử đề, nghiệm, mã hóa và điều phối
results/raw/              # Kết quả từng lượt
results/summary/          # CSV tổng hợp
report/                   # Vị trí nguồn báo cáo LaTeX
```

Bản báo cáo cuối nằm tại [`report/main.tex`](report/main.tex); tải [`report/overleaf.zip`](report/overleaf.zip) để đưa lên Overleaf và chọn **XeLaTeX**. [`report/README.md`](report/README.md) hướng dẫn biên dịch và tái tính. Gói báo cáo kèm kết quả gốc 2.160 lượt, 90 đề, chương trình phân tích và bản chụp mã tại thời điểm đo trong `report/supplement/code/`.

## 8. Kiểm thử và tái lập

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Các kiểm thử cần bộ giải tùy chọn có thể được bỏ qua nếu thiếu phụ thuộc; đọc lý do bỏ qua và kiểm tra `check_setup.py` riêng cho các cấu hình dự định chạy.

Khi lưu một thí nghiệm, giữ JSONL, danh mục đề, commit mã và thông tin phần cứng/phần mềm. Phân tích riêng theo kích thước và nhóm độ khó; ghi rõ hạn giải, số lần lặp, đơn vị bộ nhớ, các lỗi và cách tính điểm phạt. Không suy kết luận chung về cả họ SAT/ILP/CP chỉ từ một cặp mô hình–bộ giải hoặc một bộ mẫu.
