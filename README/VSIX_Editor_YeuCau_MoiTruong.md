# ⚙️ Yêu cầu môi trường

## Hệ điều hành
- Windows 10/11 (khuyến nghị bản mới).

## Python
- Python 3.9+ (khuyến nghị bản mới ổn định).
- Gợi ý cài đặt thêm: `pip install --upgrade pip`.

## Thư viện cần thiết (tuỳ phiên bản ứng dụng)
- `tkinter` (mặc định có trong Python bản Windows).
- Thư viện thao tác tệp nén/ZIP (dùng chuẩn Python).

### 🎨 Giao diện hiện đại (khuyến nghị)
- `customtkinter` — mang lại giao diện hiện đại (Dark/Light, CTk widgets).
- Cài đặt:
  ```bash
  pip install customtkinter
  ```
- Nếu chưa cài, ứng dụng sẽ tự động dùng `tkinter/ttk` cơ bản (fallback), vẫn chạy được nhưng ít hiện đại hơn.

## Cấu hình VS Code (khuyến nghị)
- Cài đặt VS Code bản mới.
- Khuyến nghị bật tiếng Việt sau khi build VSIX Việt hoá.

## Lưu ý
- Không chạy ứng dụng trong thư mục chỉ đọc.
- Nên sao lưu VSIX gốc trước khi ghi đè.
