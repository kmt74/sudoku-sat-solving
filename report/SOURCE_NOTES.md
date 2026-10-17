# Nguồn chính và cách sử dụng

Tài liệu được truy cập ngày 16--17/10/2026. Danh mục trích dẫn của báo cáo ở `references.bib`.

| Nội dung | Nguồn gốc | Điều đã kiểm tra khi viết |
|---|---|---|
| Sudoku SAT | Lynce & Ouaknine (2006), bản PDF trên trang tác giả MPI-SWS | Biến ô–số, ràng buộc Sudoku; không lấy số đo của bài gốc làm số đo của dự án |
| Binary AMO | Frisch & Giannaros (2010), bản workshop và mục công bố của University of York | Mã nhị phân riêng cho mỗi đầu vào; đúng biến thể không tối ưu mã thừa |
| Commander | Klieber & Kwon (2007), PDF trang tác giả CMU | Nhóm đại diện, có thể bỏ chiều commander → OR nhóm khi chỉ mã hóa AMO |
| Product | Chen (2010), ModRef, bản lập chỉ mục từ trang hội thảo Uppsala | Lưới hai chiều; phân biệt product dùng pairwise với product đệ quy |
| Sequential | Sinz (2005), PDF trang tác giả và DOI | Chuỗi AMO, m−1 biến phụ, 3m−4 clause |
| Bộ giải SAT | Bài PySAT SAT 2018, Glucose IJCAI 2009, MiniSat SAT 2003 | PySAT là giao diện, g3 là backend; bốn encoding ở dự án tự cài đặt |
| ILP | Ví dụ Sudoku chính thức của Gurobi | Bốn nhóm tổng bằng 1; chương trình dự án giữ clue bằng phương trình |
| Cơ chế MIP | Tài liệu IBM về branch-and-cut | Mô tả khái quát, không suy đoán các bước thực tế trên từng đề |
| CP | Tài liệu và hướng dẫn CP Optimizer của IBM; Régin AAAI 1994 | Lan truyền, all-different, minh họa lọc miền; không khẳng định nội bộ IBM dùng đúng một thuật toán cụ thể |
| CP-SAT | Perron, Didier & Gay CP 2023; tài liệu OR-Tools | Kiến trúc lai và ngữ nghĩa trạng thái; thử nghiệm một worker |
| Nhãn dữ liệu | Lagerkvist (2026), bản tác giả; repository scaled-sudoku-instances; tài liệu tham chiếu và sách Modeling and Programming with Gecode | Bảng nhãn gốc, giải thích tính nhất quán giá trị/cận/miền và shaving/channeling; phân biệt hỗ trợ cục bộ với nghiệm toàn bảng; UNSOLVED không phải UNSAT |
| Timeout | SAT Competition 2024, Tracks and Rules | Phạt 2×timeout; phần cộng build là quy ước mở rộng của báo cáo |
| RAM | psutil 7.2.2 official docs | Windows RSS=working set; có trang chia sẻ, đỉnh lấy mẫu không phải đỉnh tuyệt đối |

## Ghi chú liên kết và metadata

- Một số URL PDF hội thảo ModRef 2010 cũ của Uppsala hiện chuyển hướng khi tải trực tiếp. Nội dung bài Chen/Frisch được đối chiếu qua bản được máy tìm kiếm lập chỉ mục và mục công bố của tác giả/cơ quan; không coi trang chuyển hướng HTML là một PDF nghiên cứu. Danh mục giữ đường dẫn xuất bản gốc của Chen và đường dẫn University of York của Frisch. Nếu cần đọc offline, nên tìm bản lưu trữ theo đúng tên bài và tác giả.
- Tham khảo Simonis được nhắc trong tài liệu corpus, nhưng không chép thông tin DOI của tài liệu đó vào báo cáo khi chưa xác minh độc lập. Báo cáo trích dẫn trực tiếp tài liệu corpus đã đọc cho nhãn và phương pháp tạo đề.
- Các công thức đếm kích thước được tính lại từ mã dự án, không sao chép số đếm của một biến thể khác trong bài gốc.
- Gói không phân phối lại PDF nghiên cứu của bên thứ ba; chỉ có liên kết và thông tin trích dẫn.

## Phân biệt nguồn và kết quả của dự án

Ý tưởng mô hình và encoding có trích dẫn tại chỗ. Lựa chọn nhóm độ khó, bộ mẫu 90 đề, cấu hình solver, cách tính PAR2-total, toàn bộ bảng/hình số liệu và các phép kiểm tra nghiệm là phần triển khai/tổng hợp của dự án này. Các kết luận được giới hạn vào thiết lập đã đo.

Các hình Sudoku, Product và Hall là ví dụ minh họa tự xây dựng, vẽ trực tiếp bằng TikZ; chúng không phải đề benchmark bổ sung hay ảnh do mô hình sinh ảnh tạo. Hai hình kết quả được vẽ bằng TikZ/PGFPlots từ số liệu đã lưu.

Các tỷ lệ 65,2% điểm SATmean do timeout, 94,3%/97,9% thời gian ở nhóm 25×25 khó, và trung bình trên 80 đề còn lại được tính lại trực tiếp từ JSONL bằng `build_rq_assets.py`; đây là phân tích bổ sung trên cùng lượt đo, không phải kết quả chạy mới.
