$ErrorActionPreference = "Stop"

$path = "..\frontend\src\App.jsx"
$content = [System.IO.File]::ReadAllText((Resolve-Path $path))

$old = @"
              <p>Illustrative retention profiles</p>
"@

$new = @"
              <p>Live employee records and latest saved predictions</p>
"@

if (-not $content.Contains($old)) {
    throw "Dashboard heading not found. No changes made."
}

$content = $content.Replace($old, $new)

[System.IO.File]::WriteAllText(
    (Resolve-Path $path),
    $content,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host "Dashboard heading updated successfully." -ForegroundColor Green
