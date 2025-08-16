# Dự án Việt hóa giao diện VSCode

> Bộ công cụ dịch + đóng gói extension Tiếng Việt cho VS Code dựa trên CSV và VSIX mẫu.

## 📂 Cấu trúc chính
- `CSV/` – Toàn bộ nguồn dịch dạng CSV. Cột dùng:
  - `file, scope, key, value_zh` (sau bước dịch, `value_zh` chứa Tiếng Việt)
- `tools/`
  - `translate_with_deeptranslator.py` – Dịch tự động `key -> vi` vào `value_zh` (không cần API)
  - `build_vi_language_pack.py` – Biến CSV thành cấu trúc JSON của language pack
  - `pack_vi_from_csv.ps1` – Trình biên dịch extension từ CSV + VSIX mẫu → tạo `.vsix`
  - `export_to_translate*.ps1` / `import_translated*.ps1` – Quy trình dịch thủ công qua Google Translate (Docs)
- `work/`
  - `zh_template/` – VSIX mẫu zh (đã giải nén)
  - `vi_language_pack/` – Output extension vi (thư mục `extension/` + file `.vsix`)

## ✅ Yêu cầu
- Windows + PowerShell 5+ (có sẵn)
- Python 3.8+ (đã cài vào PATH)
- VS Code (để cài `.vsix`)

## 🚀 Quy trình 1: Dịch tự động (không cần API)
1) Cài gói cần thiết (đã thực hiện 1 lần):
   ```powershell
   python -m pip install --upgrade pip deep-translator
   ```
2) Chạy script dịch:
   ```powershell
   python tools/translate_with_deeptranslator.py --csv-dir CSV --cache work/cache_translations.json
   ```
   - Bỏ qua chuỗi “mã/ký hiệu” (không dịch, để nguyên)
   - Kết quả ghi đè `value_zh` trong tất cả `CSV/*.csv`

## 🧭 Quy trình 2: Dịch thủ công qua Google Translate (Docs)
- Xuất TXT có block đánh dấu:
  ```powershell
  powershell -ExecutionPolicy Bypass -File tools/export_to_translate_txt.ps1
  # file xuất: work/to_translate.txt
  ```
- Upload `work/to_translate.txt` lên Google Translate (Docs) → dịch sang Tiếng Việt → tải về TXT.
- Đặt tên kết quả: `work/to_translate_translated.txt`
- Nhập lại vào CSV:
  ```powershell
  powershell -ExecutionPolicy Bypass -File tools/import_translated_txt.ps1 -CsvDir CSV -InFile work/to_translate_translated.txt
  ```

## 🏗️ Quy trình 3: Biên dịch extension (.vsix) từ CSV + VSIX mẫu
- VSIX mẫu: đặt tại `zh_ex/MS-CEINTL.vscode-language-pack-zh-hans-<version>.vsix`
- Tạo `.vsix` Tiếng Việt:
  ```powershell
  powershell -ExecutionPolicy Bypass -File tools/pack_vi_from_csv.ps1 `
    -CsvDir "CSV" `
    -TemplateVsix "zh_ex/MS-CEINTL.vscode-language-pack-zh-hans-<version>.vsix" `
    -OutDir "work/vi_language_pack" `
    -OutName "vscode-language-pack-vi.vsix"
  ```
- Kết quả:
  - Thư mục: `work/vi_language_pack/extension/`
  - File cài đặt: `work/vi_language_pack/vscode-language-pack-vi.vsix`

## 💾 Cài đặt vào VS Code
- Cách 1 (UI): Extensions → “…” → Install from VSIX… → chọn file `.vsix`
- Cách 2 (CLI):
  ```powershell
  code --install-extension "work/vi_language_pack/vscode-language-pack-vi.vsix" --force
  ```
- Chọn giao diện Tiếng Việt:
  - Command Palette → “Configure Display Language” → `vi`
  - Hoặc sửa `%APPDATA%\Code\User\locale.json`:
    ```json
    { "locale": "vi" }
    ```

## 🔎 Kiểm thử & QA nhanh
- Spot-check vài chuỗi trong `CSV/main.i18n.csv`
- Có thể tạo báo cáo (tùy chọn) để lọc “translated/kept_as_key” nếu cần

## 🧩 Ghi chú kỹ thuật
- JSON sinh ra theo mẫu: trong `work/vi_language_pack/extension/translations/` và `.../translations/extensions/`
- `package.json` được sinh dựa trên metadata của VSIX mẫu (giữ version/engines, đổi `languageId` → `vi`)
- Encoding: UTF-8 (không BOM). CSV header yêu cầu `file, scope, key, value_zh`

## 🐙 Đẩy toàn bộ dự án lên GitHub
1) Tạo repo trống trên GitHub (ví dụ: `https://github.com/<user>/vscode-langpack-vi`)
2) Chạy các lệnh sau trong thư mục gốc dự án:
   ```powershell
   git init
   git add .
   git commit -m "feat: initial Vietnamese language pack from CSV"
   git branch -M main
   git remote add origin https://github.com/<user>/vscode-langpack-vi.git
   git push -u origin main
   ```
- Nếu gặp lỗi xác thực, cấu hình credential helper hoặc dùng SSH remote.

---

## 💖 Ủng hộ dự án
Bạn thấy dự án hữu ích? Mọi đóng góp sẽ giúp mình duy trì và phát triển thêm tính năng, tài liệu và chất lượng dịch. Cảm ơn bạn rất nhiều! 🙌

- Vietcombank: 1023395290

Bạn có thể ghi nội dung chuyển khoản: ủng hộ VietHoa VSCode. Mình trân trọng mọi đóng góp của bạn! 💙

Chúc bạn biên dịch vui vẻ! Nếu cần tối ưu bộ lọc “chuỗi mã/ký hiệu” hay thuật ngữ, hãy mở issue/PR trong repo. 😊
