param(
  [Parameter(Mandatory=$true)] [string] $CsvDir,
  [Parameter(Mandatory=$false)] [string] $InFile = "work/to_translate_translated.txt"
)

function Write-Info([string]$msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn([string]$msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err([string]$msg)  { Write-Host "[ERR ] $msg" -ForegroundColor Red }

if (-not (Test-Path $InFile)) { Write-Err "Input file not found: $InFile"; exit 1 }

# Read entire file as UTF-8 (no BOM enforced on read side)
$text = Get-Content -Raw -Path $InFile -Encoding UTF8
if ([string]::IsNullOrWhiteSpace($text)) { Write-Err "Input is empty: $InFile"; exit 1 }

# Split into blocks by marker
$blocks = $text -split "\n\s*\Q[[[BLOCK]]]\E\s*\n"
# If the file starts with marker, the first split item may be empty; filter empties
$blocks = $blocks | Where-Object { $_.Trim().Length -gt 0 }

if ($blocks.Count -eq 0) { Write-Err "No blocks found. Ensure markers were preserved (e.g., [[[BLOCK]]], [[[ID]]], [[[TEXT]]])."; exit 1 }

# Prepare in-memory grouping: file -> rows[]
$updatesByFile = @{}
[int]$parsed = 0
foreach ($b in $blocks) {
  # Extract ID line
  $idMatch = [regex]::Match($b, "(?m)^\Q[[[ID]]]\E\s+(.+?)\s*$")
  if (-not $idMatch.Success) { Write-Warn "Skip block: missing [[[ID]]]"; continue }
  $id = $idMatch.Groups[1].Value.Trim()
  # Expect format: filename|row_index
  $parts = $id -split '\|', 2
  if ($parts.Count -ne 2) { Write-Warn "Bad ID format: '$id'"; continue }
  $fileName = $parts[0].Trim()
  $rowIndexStr = $parts[1].Trim()
  $rowIndex = 0
  if (-not [int]::TryParse($rowIndexStr, [ref]$rowIndex)) { Write-Warn "Bad row_index in ID: '$id'"; continue }

  # Extract translated text between [[[TEXT]]] and [[[/TEXT]]]
  $textMatch = [regex]::Match($b, "(?s)\Q[[[TEXT]]]\E\s*(.*?)\s*\Q[[[/TEXT]]]\E")
  if (-not $textMatch.Success) { Write-Warn "Skip block: missing [[[TEXT]]] section for $id"; continue }
  $vi = $textMatch.Groups[1].Value
  # Normalize spaces and line endings for CSV cell
  $vi = ($vi -replace '\r', '')
  $vi = ($vi -replace '\n', ' ')
  $vi = ($vi -replace '\s+', ' ').Trim()

  if (-not $updatesByFile.ContainsKey($fileName)) { $updatesByFile[$fileName] = @() }
  $updatesByFile[$fileName] += [PSCustomObject]@{ Row=$rowIndex; Vi=$vi }
  $parsed++
}

if ($parsed -eq 0) { Write-Err "No valid blocks parsed. Aborting."; exit 1 }

# Apply updates
[int]$totalUpdated = 0
foreach ($key in $updatesByFile.Keys) {
  $fullPath = Join-Path -Path $CsvDir -ChildPath $key
  if (-not (Test-Path $fullPath)) { Write-Warn "CSV not found: $fullPath"; continue }

  $rows = Import-Csv -Path $fullPath
  if ($rows.Count -eq 0) { Write-Warn "Empty CSV: $fullPath"; continue }
  $cols = $rows[0].PsObject.Properties.Name
  if (-not ($cols -contains 'value_zh')) { Write-Warn "No value_zh column in: $fullPath"; continue }

  $updates = $updatesByFile[$key]
  $updatedHere = 0
  foreach ($u in $updates) {
    if ($u.Row -ge 0 -and $u.Row -lt $rows.Count) {
      $rows[$u.Row].value_zh = [string]$u.Vi
      $updatedHere++
    } else {
      Write-Warn "Row out of range $($u.Row) for $fullPath (rows=$($rows.Count))"
    }
  }

  $rows | Export-Csv -Path $fullPath -NoTypeInformation -Encoding UTF8
  $totalUpdated += $updatedHere
  Write-Info "Updated $updatedHere rows in $fullPath"
}

Write-Info "Total updated rows: $totalUpdated"
