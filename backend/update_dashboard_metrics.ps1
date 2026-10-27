$ErrorActionPreference = "Stop"

$path = (Resolve-Path "..\frontend\src\App.jsx").Path
$content = [System.IO.File]::ReadAllText($path)

$oldAttrition = '<MetricCard label="Attrition rate" value="8.4%" change="-1.2%" positive icon={TrendingUp} tone="mint" detail="Illustrative demo value" />'
$newAttrition = '<MetricCard label="Attrition rate" value="Unavailable" icon={TrendingUp} tone="mint" detail="Live attrition rate metric is not available from the current dashboard API." />'

$oldPositions = '<MetricCard label="Open positions" value="24" change="+3 roles" positive icon={BriefcaseBusiness} tone="amber" detail="Illustrative demo value" />'
$newPositions = '<MetricCard label="Open positions" value="Unavailable" icon={BriefcaseBusiness} tone="amber" detail="Open positions data is not available from the current backend API." />'

$attritionCount = ([regex]::Matches($content, [regex]::Escape($oldAttrition))).Count
$positionsCount = ([regex]::Matches($content, [regex]::Escape($oldPositions))).Count

if ($attritionCount -ne 1 -or $positionsCount -ne 1) {
    throw "Expected exact card code was not found once each. File unchanged. Attrition matches: $attritionCount; Open positions matches: $positionsCount"
}

$updated = $content.Replace($oldAttrition, $newAttrition).Replace($oldPositions, $newPositions)

Copy-Item -LiteralPath $path -Destination "$path.metrics-next-backup" -Force
[System.IO.File]::WriteAllText($path, $updated, [System.Text.UTF8Encoding]::new($false))

Write-Host "SUCCESS: Attrition rate and Open positions now show Unavailable instead of demo numbers." -ForegroundColor Green
Write-Host "Backup: $path.metrics-next-backup"
