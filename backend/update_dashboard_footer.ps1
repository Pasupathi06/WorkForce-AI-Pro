$ErrorActionPreference = "Stop"

$path = (Resolve-Path "..\frontend\src\App.jsx").Path
$content = [System.IO.File]::ReadAllText($path)

$old = @"
        <div className="dashboard-footnote">
          <CircleAlert size={15} />
          Dashboard cards, charts, and risk scores are illustrative demo values,
          not live workforce analytics.
        </div>
"@

$new = @"
        <div className="dashboard-footnote">
          <CircleAlert size={15} />
          Employee counts and high-risk prediction records are loaded from the backend when available.
          Workforce trends and other illustrative charts are demo data; unavailable metrics are not shown as real values.
        </div>
"@

if (-not $content.Contains($old)) {
    throw "Expected dashboard footer block not found. File unchanged."
}

$updated = $content.Replace($old, $new)

Copy-Item -LiteralPath $path -Destination "$path.footer-backup" -Force
[System.IO.File]::WriteAllText($path, $updated, [System.Text.UTF8Encoding]::new($false))

Write-Host "SUCCESS: Dashboard footer updated." -ForegroundColor Green
Write-Host "Backup: $path.footer-backup"
