param(
  [Parameter(Mandatory=$true)] [string] $CsvDir,
  [Parameter(Mandatory=$true)] [string] $SubscriptionKey,
  [Parameter(Mandatory=$true)] [string] $Region,
  [Parameter(Mandatory=$false)] [int] $BatchSize = 80,
  [Parameter(Mandatory=$false)] [switch] $WhatIf
)

# Azure Translator endpoint
$Endpoint = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&from=en&to=vi"

function Write-Info([string]$msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn([string]$msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err([string]$msg) { Write-Host "[ERR ] $msg" -ForegroundColor Red }

# Heuristic to detect code-like or machine symbols to skip translating
function Is-CodeLike([string] $text) {
  if ([string]::IsNullOrWhiteSpace($text)) { return $true }

  # Common placeholders and tokens: {0}, ${var}, %s, %d, \n, <tag>, http://, file paths, camelCase.with.dots, ALL_CAPS, GUIDs, hex
  $patterns = @(
    '\\{\d+\\}',              # {0}, {1}
    '\\$\w+',                  # $var
    '%[sdifoxX]',                # %s, %d
    '\\n|\\r|\\t',           # escape sequences
    '<[^>]+>',                   # HTML/XML tags
    'https?://',                 # urls
    '(?i)[a-z]:\\\\',         # windows path like C:\
    '(?i)\\\\\\\\|/',     # path separators presence
    '[A-Za-z]+\.[A-Za-z0-9_\-]+', # dotted identifiers
    '^[A-Z0-9_\\-]{3,}$',      # ALL_CAPS tokens
    '^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$', # GUID
    '0x[0-9a-fA-F]+'             # hex
  )

  foreach ($p in $patterns) { if ($text -match $p) { return $true } }

  # If too short or mostly non-letters, consider code-like
  $letters = ($text -replace '[^A-Za-z]', '').Length
  $ratio = 0
  if ($text.Length -gt 0) { $ratio = $letters / $text.Length }
  if ($text.Trim().Length -lt 2 -or $ratio -lt 0.3) { return $true }

  return $false
}

function Protect-Placeholders([string] $text) {
  # Replace placeholders with sentinel tokens to avoid mistranslation
  $map = @{}
  $idx = 0
  $pattern = '(\\{\d+\\}|%[sdifoxX]|\$\w+|\{\w+\}|\$\{[^}]+\})'
  $protected = [regex]::Replace($text, $pattern, {
    param($m)
    $token = "__PH$idx__"
    $map[$token] = $m.Value
    $script:idx += 1
    return $token
  })
  return @{ Text = $protected; Map = $map }
}

function Restore-Placeholders([string] $text, $map) {
  foreach ($k in $map.Keys) { $text = $text -replace [regex]::Escape($k), [regex]::Escape($map[$k]) }
  return $text
}

function Invoke-TranslateBatch([string[]] $texts) {
  $body = @()
  foreach ($t in $texts) { $body += @{ Text = $t } }
  $json = $body | ConvertTo-Json -Depth 5

  $headers = @{
    'Ocp-Apim-Subscription-Key' = $SubscriptionKey
    'Ocp-Apim-Subscription-Region' = $Region
    'Content-Type' = 'application/json; charset=UTF-8'
  }
  try {
    $resp = Invoke-RestMethod -Method Post -Uri $Endpoint -Headers $headers -Body $json -TimeoutSec 60
    return $resp
  } catch {
    Write-Err "Translation API error: $($_.Exception.Message)"
    throw
  }
}

function Process-File([string] $filePath) {
  Write-Info "Processing: $filePath"
  $rows = Import-Csv -Path $filePath
  if ($rows.Count -eq 0) { Write-Warn "Empty: $filePath"; return }
  $cols = $rows[0].PsObject.Properties.Name
  if (-not ($cols -contains 'key' -and $cols -contains 'value_zh')) { Write-Warn "Skipped (no key/value_zh): $filePath"; return }

  # Build indices of rows to translate
  $items = @()
  for ($i=0; $i -lt $rows.Count; $i++) {
    $k = [string]$rows[$i].key
    if ([string]::IsNullOrWhiteSpace($k)) { continue }
    if (Is-CodeLike $k) {
      # Keep as original (overwrite per requirement but identical to key)
      $rows[$i].value_zh = $k
      continue
    }
    $prot = Protect-Placeholders $k
    $items += [PSCustomObject]@{ Index=$i; Original=$k; Protected=$prot.Text; Map=$prot.Map }
  }

  $translated = @{}
  for ($p = 0; $p -lt $items.Count; $p += $BatchSize) {
    $batch = $items[$p..([Math]::Min($p+$BatchSize-1, $items.Count-1))]
    $texts = $batch.Protected

    if ($WhatIf) { Write-Info "(WhatIf) Would translate $($texts.Count) items"; continue }

    $resp = Invoke-TranslateBatch -texts $texts
    # Azure response: array of results, each has translations[0].text
    for ($j=0; $j -lt $batch.Count; $j++) {
      $vi = [string]$resp[$j].translations[0].text
      $translated[$batch[$j].Index] = $vi
    }
    Start-Sleep -Milliseconds 200
  }

  # Apply translations
  foreach ($it in $items) {
    if ($WhatIf) {
      Write-Host ("Preview: '{0}' => '{1}'" -f $it.Original, $it.Original) -ForegroundColor DarkGray
      continue
    }
    $vi = $translated[$it.Index]
    if (-not [string]::IsNullOrWhiteSpace($vi)) {
      $vi = Restore-Placeholders $vi $it.Map
      # Minor post-fix: trim, normalize spaces
      $vi = ($vi -replace '\\s+', ' ').Trim()
      $rows[$it.Index].value_zh = $vi
    } else {
      $rows[$it.Index].value_zh = $it.Original
    }
  }

  if (-not $WhatIf) {
    $rows | Export-Csv -Path $filePath -NoTypeInformation -Encoding UTF8
    Write-Info "Updated: $filePath"
  } else {
    Write-Info "(WhatIf) Skipped writing: $filePath"
  }
}

# Main
$files = Get-ChildItem -Path $CsvDir -Filter *.csv -File
if ($files.Count -eq 0) { Write-Warn "No CSV files found in $CsvDir"; exit 0 }
foreach ($f in $files) { Process-File -filePath $f.FullName }
