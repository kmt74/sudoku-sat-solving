# Báo cáo cuối: Giải Sudoku bằng SAT, ILP và CP

Nguồn chính: [`main.tex`](main.tex). Bản này dùng nội dung chốt trong `mode_title__3_.zip`; phần đầu đã đổi từ “ARTICLE INFO” thành “THÔNG TIN BÁO CÁO”. Thông tin tác giả và nội dung nghiên cứu được giữ theo bản chốt.

## Biên dịch

**Overleaf:** tải [`overleaf.zip`](overleaf.zip), tạo project từ ZIP, chọn compiler **XeLaTeX** và main document `main.tex`. Giữ nguyên các thư mục `figures/` và `tables/`. Thư mục này có sẵn class/style CAS và thư mục tài liệu tham khảo.

**TeX Live/MiKTeX:** mở terminal tại `report/` rồi chạy:

```text
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

Hình được vẽ bằng TikZ/PGFPlots; không cần ảnh hoặc PDF ngoài. Nếu không có Times New Roman, nguồn tự dùng TeX Gyre Termes có trong TeX Live/Overleaf.

## Dữ liệu và khả năng tái lập

- [`data/all-results.jsonl`](data/all-results.jsonl): 2.160 lượt đo; 2.120 SOLVED, 40 TIMEOUT, không có ERROR/UNSAT.
- [`data/manifest.csv`](data/manifest.csv) và [`data/puzzles/`](data/puzzles/): danh mục và 90 đề, giữ ID/nhãn gốc/nguồn.
- [`data/LICENSE.upstream`](data/LICENSE.upstream): giấy phép dữ liệu nguồn.
- [`SOURCE_NOTES.md`](SOURCE_NOTES.md), [`references.bib`](references.bib): nguồn tham khảo và cách sử dụng.
- [`analyze.py`](analyze.py): đối chiếu dữ liệu, nghiệm và các chỉ số.
- [`build_report_assets.py`](build_report_assets.py), [`build_rq_assets.py`](build_rq_assets.py): tái tính bảng và hình từ kết quả đã lưu; không chạy lại bộ giải.
- [`supplement/code/`](supplement/code/), [`supplement/provenance.json`](supplement/provenance.json): bản chụp mã dùng cho phép đo và thông tin phiên bản. Bản chụp giữ cả những thay đổi điều phối chưa commit tại thời điểm chạy.
- [`supplement/selection/`](supplement/selection/): cách chọn và truy xuất mẫu.
- [`SHA256SUMS.txt`](SHA256SUMS.txt): mã băm các tệp của gói báo cáo.

Để tái tính, cài `matplotlib` và `numpy`, rồi chạy trong `report/`:

```text
python -m pip install matplotlib numpy
python -X utf8 analyze.py
python -X utf8 build_report_assets.py
```

Các lệnh sinh lại bảng/hình và có thể ghi đè các tệp tương ứng. Bản chốt để biên dịch đã có đủ tệp, nên không cần chạy bước tái tính nếu chỉ đọc hoặc nộp báo cáo. Dữ liệu thí nghiệm là các lượt đã chạy ngày 15/10/2026; việc cập nhật báo cáo không tạo lượt giải mới.
