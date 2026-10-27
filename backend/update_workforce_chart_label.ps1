$ErrorActionPreference = "Stop"

$path = (Resolve-Path "..\frontend\src\App.jsx").Path
$content = [System.IO.File]::ReadAllText($path)

$old = '<p>Illustrative employee and attrition trends</p>'
$new = '<p>Illustrative demo data — not live historical analytics</p>'

$count = ([regex]::Matches($content, [regex]::Escape($old))).Count
if ($count -ne 1) {
    throw "Expected one Workforce overview description; found $count. File unchanged."
}

$updated = $content.Replace($old, $new)

Copy-Item -LiteralPath $path -Destination "$path.workforce-chart-backup" -Force
[System.IO.File]::WriteAllText($path, $updated, [System.Text.UTF8Encoding]::new($false))

Write-Host "SUCCESS: Workforce overview now clearly identifies its data as illustrative." -ForegroundColor Green
Write-Host "Backup: $path.workforce-chart-backup"
