param(
    [Parameter(Mandatory=$true)] [string]$CsvDir,
    [Parameter(Mandatory=$true)] [string]$TemplateVsix,
    [Parameter(Mandatory=$false)] [string]$OutDir = "work/vi_language_pack",
    [Parameter(Mandatory=$false)] [string]$OutName = "vscode-language-pack-vi.vsix"
)

$ErrorActionPreference = "Stop"

function Resolve-FullPath([string]$p) {
    return (Resolve-Path -LiteralPath $p).Path
}

# Normalize paths
$CsvDir = Resolve-FullPath $CsvDir
$TemplateVsix = Resolve-FullPath $TemplateVsix
$OutDir = Resolve-FullPath $OutDir

# Directories
$ExtractDir = Join-Path $OutDir "_template_extract"
$OutExtDir = Join-Path $OutDir "extension"
$PackRoot = Join-Path $OutDir "pack_root"
$VsixPath = Join-Path $OutDir $OutName
$ZipTmp = [System.IO.Path]::ChangeExtension($VsixPath, ".zip")
${TemplateZip} = Join-Path $OutDir "_template.zip"

Write-Host "[1/5] Chuẩn bị thư mục đầu ra: $OutDir"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
if (Test-Path $ExtractDir) { Remove-Item -Recurse -Force $ExtractDir }
if (Test-Path $OutExtDir) { Remove-Item -Recurse -Force $OutExtDir }
if (Test-Path $PackRoot) { Remove-Item -Recurse -Force $PackRoot }
if (Test-Path $TemplateZip) { Remove-Item -Force $TemplateZip }

Write-Host "[2/5] Giải nén VSIX mẫu: $TemplateVsix"
# PowerShell chỉ hỗ trợ .zip, vì vậy sao chép VSIX thành .zip tạm rồi giải nén
Copy-Item -LiteralPath $TemplateVsix -Destination $TemplateZip -Force
Expand-Archive -LiteralPath $TemplateZip -DestinationPath $ExtractDir -Force
$TemplateExtensionDir = Join-Path $ExtractDir "extension"
if (-not (Test-Path $TemplateExtensionDir)) {
    throw "Không tìm thấy thư mục 'extension' bên trong VSIX mẫu tại: $TemplateExtensionDir"
}

Write-Host "[3/5] Sinh extension Tiếng Việt từ CSV: $CsvDir"
# Gọi Python builder
$python = "python"
try {
    & $python --version | Out-Null
} catch {
    throw "Không tìm thấy Python trong PATH. Hãy cài Python 3 và chạy lại."
}

$builder = Join-Path (Split-Path $PSCommandPath -Parent) "build_vi_language_pack.py"
if (-not (Test-Path $builder)) {
    throw "Không tìm thấy builder: $builder"
}

& $python $builder --csv-dir $CsvDir --template-ext $TemplateExtensionDir --out-dir $OutExtDir

Write-Host "[4/5] Đóng gói VSIX đúng cấu trúc (root chứa 'extension/')"
if (Test-Path $VsixPath) { Remove-Item -Force $VsixPath }
if (Test-Path $ZipTmp) { Remove-Item -Force $ZipTmp }

# Tạo pack root và copy thư mục extension vào
New-Item -ItemType Directory -Path $PackRoot | Out-Null
Copy-Item -Recurse -Force -Path $OutExtDir -Destination (Join-Path $PackRoot "extension")

# Nén và đổi tên .zip -> .vsix
Compress-Archive -Path (Join-Path $PackRoot '*') -DestinationPath $ZipTmp -Force
Rename-Item -Path $ZipTmp -NewName (Split-Path $VsixPath -Leaf) -Force

# Kiểm tra cấu trúc VSIX
$InspectDir = Join-Path $OutDir "_inspect"
if (Test-Path $InspectDir) { Remove-Item -Recurse -Force $InspectDir }
# Expand-Archive không hỗ trợ .vsix trực tiếp, tạo bản sao .zip tạm để kiểm tra
$OutVsixZip = Join-Path $OutDir "_out_vsix.zip"
if (Test-Path $OutVsixZip) { Remove-Item -Force $OutVsixZip }
Copy-Item -LiteralPath $VsixPath -Destination $OutVsixZip -Force
Expand-Archive -LiteralPath $OutVsixZip -DestinationPath $InspectDir -Force
if (-not (Test-Path (Join-Path $InspectDir 'extension/package.json'))) {
    throw "Gói VSIX không hợp lệ: thiếu extension/package.json"
}

# Dọn file tạm
if (Test-Path $TemplateZip) { Remove-Item -Force $TemplateZip }
if (Test-Path $OutVsixZip) { Remove-Item -Force $OutVsixZip }

Write-Host "[5/5] Hoàn tất: " -NoNewline
Write-Host $VsixPath -ForegroundColor Green
Write-Host "Cài đặt bằng VS Code CLI:"
Write-Host "  code --install-extension `"$VsixPath`" --force"
