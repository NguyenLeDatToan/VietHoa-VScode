# 🇻🇳 Gói Việt hoá VS Code — VietHoaVSCodeV2.0

> Công cụ và tài liệu phục vụ Việt hoá VS Code. Tài liệu chi tiết đặt trong thư mục `README/` để gọn gàng.

### 🔗 Quick Links
- 📘 Hướng dẫn sử dụng VSIX Editor: `README/VSIX_Editor_HuongDan.md`
- ⚙️ Yêu cầu môi trường: `README/VSIX_Editor_YeuCau_MoiTruong.md`
- 📦 Cài đặt VSIX vào VS Code: `README/VSCode_VSIX_CaiDat_HuongDan.md`

---

## 🧰 VSIX Editor — Tính năng
- Mở VSIX, liệt kê nội dung; hiển thị JSON/`*.code-snippets` dạng lưới (path | value).
- Sửa trực tiếp (double‑click), lọc path/value, tìm & sửa hàng loạt.
- Xem trước tệp không phải JSON; cho phép chỉnh sửa `.md/.markdown` khi bật tuỳ chọn phù hợp.
- Build/Lưu VSIX mới; tuỳ chọn tự tăng version (patch) để cài thử nhanh.

### 🎨 Giao diện hiện đại
- Hỗ trợ Dark/Light mode; UI hiện đại khi có `customtkinter` (fallback sang `tkinter/ttk` nếu chưa cài).
- Khu lọc file bên trái đã làm mới với bố cục lưới rõ ràng: lọc theo chức năng, loại, và tên (có co giãn chiều ngang).

Xem hướng dẫn chi tiết: `README/VSIX_Editor_HuongDan.md`
Yêu cầu môi trường (bao gồm cài đặt UI hiện đại): `README/VSIX_Editor_YeuCau_MoiTruong.md`

---

## 📦 Tệp lớn (.vsix) & Git LFS
- Khi chia sẻ repo công khai, khuyến nghị dùng Git LFS cho `*.vsix`.
- Khi clone, nên chạy:
  ```powershell
  git lfs install
  git lfs pull
  ```
- Tránh dùng "Download ZIP" nếu cần nhận đủ dữ liệu LFS.

---

## 🚀 Bắt đầu nhanh
- Yêu cầu môi trường: `README/VSIX_Editor_YeuCau_MoiTruong.md`
- Chạy ứng dụng:
  ```bash
  python UItranslate/vsix_editor.py
  ```
- Quy trình: Mở VSIX → sửa → lưu/build VSIX mới.

---

## 🤝 Đóng góp & Góp ý
- Hoan nghênh góp ý về tính năng, UI/UX, hiệu năng và tài liệu.
- Khi báo lỗi: nêu bước tái hiện, môi trường (Python/Windows/VS Code) và ảnh chụp nếu có.

---

## 🙏 Lời cảm ơn
Gói ngôn ngữ tiếng Việt này là kết quả của nỗ lực Việt hoá dựa trên cộng đồng "bởi cộng đồng, vì cộng đồng". Xin cảm ơn mọi người đã đóng góp cho dự án.

---

## 👤 Tác giả

- Trình viên:
`HêuBếu`
`LeeSang (Mr.Nipo)`
`Tonly`

- Dịch Thuật:
`Như Ý`
`Lita (Kim Huyền)`
