param(
  [Parameter(Mandatory=$true)] [string] $CsvDir,
  [Parameter(Mandatory=$false)] [string] $InFile = "work/to_translate_translated.csv"
)

function Write-Info([string]$msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn([string]$msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err([string]$msg)  { Write-Host "[ERR ] $msg" -ForegroundColor Red }

if (-not (Test-Path $InFile)) { Write-Err "Input file not found: $InFile"; exit 1 }
$items = Import-Csv -Path $InFile
if ($items.Count -eq 0) { Write-Warn "No rows in $InFile"; exit 0 }

# Validate columns
$cols = $items[0].PsObject.Properties.Name
foreach ($req in @('file','row_index','key')) { if (-not ($cols -contains $req)) { Write-Err "Missing column '$req' in $InFile"; exit 1 } }
# Accept either 'vi' or 'translated' as the translated column
$translatedCol = if ($cols -contains 'vi') { 'vi' } elseif ($cols -contains 'translated') { 'translated' } else { '' }
if ([string]::IsNullOrWhiteSpace($translatedCol)) { Write-Err "Missing translated column: expected 'vi' or 'translated'"; exit 1 }

# Group items by file to reduce IO
$byFile = $items | Group-Object -Property file

foreach ($group in $byFile) {
  $fileName = $group.Name
  $fullPath = Join-Path -Path $CsvDir -ChildPath $fileName
  if (-not (Test-Path $fullPath)) { Write-Warn "Skip missing CSV: $fullPath"; continue }

  $rows = Import-Csv -Path $fullPath
  if ($rows.Count -eq 0) { Write-Warn "Empty CSV: $fullPath"; continue }
  $csvCols = $rows[0].PsObject.Properties.Name
  if (-not ($csvCols -contains 'value_zh')) { Write-Warn "Skip (no value_zh): $fullPath"; continue }

  $updatedCount = 0
  foreach ($it in $group.Group) {
    $idx = 0
    if (-not [int]::TryParse([string]$it.row_index, [ref]$idx)) { Write-Warn "Bad row_index for $fileName: '$($it.row_index)'"; continue }
    if ($idx -lt 0 -or $idx -ge $rows.Count) { Write-Warn "Out-of-range row_index $idx for $fileName (rows=$($rows.Count))"; continue }

    $translated = [string]$it.$translatedCol
    if ([string]::IsNullOrWhiteSpace($translated)) { continue }

    # Normalize spaces
    $translated = ($translated -replace '\\s+', ' ').Trim()
    $rows[$idx].value_zh = $translated
    $updatedCount++
  }

  $rows | Export-Csv -Path $fullPath -NoTypeInformation -Encoding UTF8
  Write-Info "Updated $updatedCount rows in $fullPath"
}
