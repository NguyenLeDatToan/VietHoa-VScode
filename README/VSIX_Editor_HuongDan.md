# 🧰 VSIX Editor — Hướng dẫn sử dụng

> Công cụ hỗ trợ mở/chỉnh sửa nhanh nội dung trong gói VSIX của VS Code.

## ✨ Tính năng chính
- Mở gói VSIX và liệt kê toàn bộ nội dung.
- Tự nhận diện và hiển thị bảng 2 cột cho JSON/`*.code-snippets` (path | value).
- Sửa trực tiếp giá trị (double‑click), lọc theo path/value, tìm & sửa hàng loạt trên nhiều file JSON.
- Xem trước (preview) các tệp không phải JSON; cho phép chỉnh sửa văn bản với `.md/.markdown` khi bật tuỳ chọn "Sửa văn bản (.md)".
- Lưu file hiện tại ra đĩa.
- Build/Lưu ra VSIX mới, tuỳ chọn tự tăng version (patch) để cài thử trong VS Code. Có thể chọn đúng file VSIX gốc ở hộp thoại lưu để ghi đè.

### 🎨 Giao diện & Chế độ màu
- Hỗ trợ Dark/Light mode (có nút bật/tắt trong thanh công cụ).
- Nếu có `customtkinter` → giao diện hiện đại (CTk widgets). Nếu chưa cài → tự động dùng `tkinter/ttk` (fallback) và vẫn chạy bình thường.

### 🧭 Bộ lọc tệp (bố cục lưới rõ ràng)

## 🔍 Chức năng chi tiết
- 🗂️ Quản lý gói VSIX:
  - Mở gói VSIX, đọc cấu trúc, liệt kê đầy đủ tệp.
  - Xem nhanh metadata/manifest (nếu có) để hỗ trợ build.
- 🧭 Duyệt & Lọc tệp (panel trái):
  - Lọc theo "Chức năng" (nhóm tệp), "Loại" (phần mở rộng), và "Tên" (từ khoá).
  - Bố cục lưới rõ ràng; ô nhập co giãn; nút Lọc/Xoá lọc tách riêng, có separator.
  - Danh sách tệp có thanh cuộn; chọn tệp để xem nội dung bên phải.
- 👀 Xem trước & Chỉnh sửa nội dung:
  - JSON/`*.code-snippets`: hiển thị dạng bảng 2 cột (path | value).
  - Double‑click vào cột value để sửa inline; Enter=Lưu, Esc=Huỷ; tự đóng khi resize.
  - Markdown (`.md/.markdown`): bật tuỳ chọn "Sửa văn bản (.md)" để cho phép chỉnh sửa và lưu.
  - Các tệp khác: xem preview (chỉ đọc nếu không hỗ trợ chỉnh sửa).
- 🔎🔁 Tìm & Thay trên JSON (nhiều tệp):
  - Tìm từ khoá và thay thế hàng loạt trên tất cả tệp JSON đang mở.
  - Có thể hiển thị kết quả/nhật ký theo tệp/hàng thay đổi (nếu UI có log).
  - Phạm vi tác động:
    - Áp dụng cho các tệp JSON thuộc gói VSIX đang mở.
    - Không ảnh hưởng tới tệp nhị phân/ảnh (`.png`, `.jpg`, ...).
    - Không hỗ trợ hoàn tác hàng loạt trong ứng dụng → hãy sao lưu VSIX hoặc làm việc trên bản sao trước khi chạy thay thế diện rộng.
    - Khuyến nghị giới hạn phạm vi bằng cách lọc danh sách tệp trước khi thực hiện.
- 💾 Lưu & Xuất bản:
  - Lưu nội dung tệp hiện tại ra đĩa (nếu cho phép chỉnh sửa).
  - Build/Lưu VSIX mới; hỗ trợ tự tăng version (patch) để cài thử nhanh.
  - Cho phép lưu đè vào VSIX gốc (tuỳ chọn) để cập nhật bản cài đặt.
- 🌓 Giao diện & Trải nghiệm:
  - Dark/Light mode có thể bật/tắt nhanh trong thanh công cụ.
  - Hỗ trợ `customtkinter` cho giao diện hiện đại; fallback `tkinter/ttk` nếu chưa cài.
  - Bố cục PanedWindow 2 panel, có minsize để tránh chồng lấn.

## 🚀 Quy trình nhanh
1) Mở ứng dụng VSIX Editor.
2) Chọn tệp VSIX (File VSIX gốc được tải kèm trong thư mục EXPORT).
3) Chọn tệp JSON cần sửa → chỉnh sửa ngay trên lưới.
4) Lưu thay đổi hoặc Build VSIX mới (có thể bật auto bump version patch).

## 🧩 Mẹo & Lưu ý
- Khi sửa `.md/.markdown`, bật tuỳ chọn "Sửa văn bản (.md)" để ghi nội dung.
- Khi Build, có thể lưu đè lên VSIX gốc (dễ cài đặt lại trong VS Code).
- Nếu gặp lỗi file lớn, hãy đảm bảo đủ quyền ghi và dung lượng ổ đĩa.

### ⌨️ Phím tắt hữu ích
- Trong editor inline: Enter = Lưu, Esc = Huỷ.

---

## 🆘 Khắc phục lỗi thường gặp
- Không hiện bảng 2 cột: Kiểm tra tệp có phải JSON/`*.code-snippets` hợp lệ.
- Không lưu được VSIX: Đóng VS Code nếu đang dùng file, thử lưu đường dẫn khác.
- Bảng không cập nhật: Dùng Refresh/Reload hoặc mở lại VSIX.

---

## 📚 Tài liệu liên quan
- Yêu cầu môi trường: `README/VSIX_Editor_YeuCau_MoiTruong.md`
- Hướng dẫn cài VSIX: `README/VSCode_VSIX_CaiDat_HuongDan.md`
 - Tổng quan dự án: `README.md`
