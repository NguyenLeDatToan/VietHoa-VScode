param(
  [Parameter(Mandatory=$true)] [string] $CsvDir,
  [Parameter(Mandatory=$false)] [string] $OutFile = "work/to_translate.csv"
)

function Write-Info([string]$msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn([string]$msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }

function Is-CodeLike([string] $text) {
  if ([string]::IsNullOrWhiteSpace($text)) { return $true }
  $patterns = @(
    '\\{\d+\\}',              # {0}
    '\\$\w+',                  # $var
    '%[sdifoxX]',                # %s
    '\\n|\\r|\\t',           # escapes
    '<[^>]+>',                   # tags
    'https?://',                 # url
    '(?i)[a-z]:\\\\',         # C:\
    '(?i)\\\\\\\\|/',     # path sep
    '[A-Za-z]+\.[A-Za-z0-9_\-]+', # dotted ids
    '^[A-Z0-9_\\-]{3,}$',      # ALL_CAPS
    '^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$', # GUID
    '0x[0-9a-fA-F]+'             # hex
  )
  foreach ($p in $patterns) { if ($text -match $p) { return $true } }
  $letters = ($text -replace '[^A-Za-z]', '').Length
  $ratio = 0
  if ($text.Length -gt 0) { $ratio = $letters / $text.Length }
  if ($text.Trim().Length -lt 2 -or $ratio -lt 0.3) { return $true }
  return $false
}

$fullOut = if ([System.IO.Path]::IsPathRooted($OutFile)) { $OutFile } else { Join-Path -Path (Get-Location) -ChildPath $OutFile }
$workDir = [System.IO.Path]::GetDirectoryName($fullOut)
if (-not (Test-Path $workDir)) { New-Item -ItemType Directory -Path $workDir | Out-Null }

$results = New-Object System.Collections.Generic.List[object]
$files = Get-ChildItem -Path $CsvDir -Filter *.csv -File
if ($files.Count -eq 0) { Write-Warn "No CSV files in $CsvDir"; exit 0 }

foreach ($f in $files) {
  $rows = Import-Csv -Path $f.FullName
  if ($rows.Count -eq 0) { continue }
  $cols = $rows[0].PsObject.Properties.Name
  if (-not ($cols -contains 'key' -and $cols -contains 'value_zh')) { continue }

  for ($i=0; $i -lt $rows.Count; $i++) {
    $k = [string]$rows[$i].key
    if ([string]::IsNullOrWhiteSpace($k)) { continue }
    if (Is-CodeLike $k) { continue }
    $results.Add([PSCustomObject]@{ file = $f.Name; row_index = $i; key = $k })
  }
}

if ($results.Count -eq 0) { Write-Warn "Nothing to export."; exit 0 }
$results | Export-Csv -Path $fullOut -NoTypeInformation -Encoding UTF8
Write-Info "Exported $($results.Count) rows to $fullOut"
