# Bộ đề benchmark Sudoku

Bộ này gồm **90 đề**: mỗi kích thước `9x9`, `16x16`, `25x25` có 10 đề cho
mỗi nhóm `easy`, `medium`, `hard`. Mọi đề đến từ
[Scaled Sudoku Instances](https://github.com/zayenz/scaled-sudoku-instances)
tại commit `a8596ccaa29587c821c1ccf29225a66a7b4d5a13`.
Giấy phép nguồn là MIT; xem [LICENSE.upstream](LICENSE.upstream).

## Ý nghĩa độ khó

Ba nhóm là **quy tắc của thí nghiệm**, dựa trên nhãn suy diễn ràng buộc gốc:

| Nhóm | `hardness_level` gốc |
|---|---|
| `easy` | `Val`, `ValBS`, `ValDS`, `ValChan` |
| `medium` | `Bnd`, `BndBS`, `BndDS`, `BndChan` |
| `hard` | `Dom`, `DomBS`, `DomDS`, `UNSOLVED` |

Đây không phải thang độ khó cho người chơi và cũng không bảo đảm thời gian giải
tăng đều ở tất cả solver. `UNSOLVED` chỉ có nghĩa là các cấu hình suy diễn được
nguồn thử không giải hết đề mà không tìm kiếm; đề vẫn có nghiệm duy nhất theo
nguồn. Phân tích độ khó nên thực hiện riêng cho từng kích thước.

## Cách chọn và nguồn gốc

- Seed chọn mẫu: `20261015`. Mỗi nhóm có 10 đề, với quota theo nhãn gốc để
  **cả 12 nhãn gốc** đều có mặt trong bộ 90 đề. Đây là mẫu cân bằng để so sánh,
  không đại diện cho tần suất các nhãn trong toàn bộ corpus.
- `9x9`: cả 30 đề lấy từ `base/` để có đủ nhãn `Dom` hiếm gặp.
- `16x16`: 10 đề `hard` lấy từ `base/`; 20 đề còn lại lấy từ
  `walks/variants/`.
- `25x25`: 3 đề `hard` nhãn `UNSOLVED` lấy từ `base/`; 27 đề còn lại lấy từ
  `walks/variants/`. Các đề gốc `25x25` đều thuộc nhóm cần tìm kiếm theo
  [bài báo của tác giả](https://zayenz.se/papers/Lagerkvist_ModRef_2026_Scaling_Sudoku.pdf).
- **90 đề có 90 `source_root` khác nhau**; không chọn hai biến thể cùng một
  đề gốc. Chi tiết ID, nhãn, số gợi ý, đường dẫn nguồn, commit và SHA-256 của
  file nguồn ở [manifest.csv](manifest.csv).

Các file `.sdk.txt` của nguồn được chuyển thành bảng số: `.` → `0`, `1`–`9`
giữ nguyên, `A` → `10`, `B` → `11`, v.v. Mỗi file JSON giữ `difficulty`,
`hardness_level`, `source_path` và `source_root`. Khi nhập dữ liệu, mọi bảng
đã được kiểm tra kích thước, số gợi ý, trùng đề và đối chiếu với nghiệm có
sẵn trong metadata nguồn bằng `validate_solution`. Việc nghiệm là duy nhất
dựa trên kiểm tra đã công bố của nguồn; bộ nhập này không chứng minh lại
tính duy nhất.

## Chạy thử

Từ thư mục gốc repo, có thể chạy một nhóm trước:

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py --data data/benchmark/9x9/easy --repeats 1 --time-limit 30 --measure-memory
```

Khi đã kiểm tra giới hạn thời gian trên máy của mình, chạy toàn bộ bộ đề:

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py --data data/benchmark --repeats 3 --time-limit 30 --measure-memory
```

Không dùng `--data data` cho lượt benchmark chính vì đường dẫn đó còn chứa
các đề `smoke` của repo.
