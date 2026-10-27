$ErrorActionPreference = "Stop"

$path = ".\frontend\src\App.jsx"
$backup = ".\frontend\src\App.jsx.backup-before-analytics-cleanup"

$content = Get-Content -Path $path -Raw

if (-not (Test-Path $path)) {
    throw "App.jsx file not found."
}

if ($content -notmatch 'Monthly hiring') {
    throw "Live Analytics section was not found. No changes made."
}

if ($content -notmatch 'Workforce trend') {
    throw "Expected old demo Analytics section was not found. No changes made."
}

$oldDemoMarker = '      return (' + "`r`n" + '        <section className="analytics-page">'
$oldDemoMarkerLF = '      return (' + "`n" + '        <section className="analytics-page">'

$countCRLF = ([regex]::Matches($content, [regex]::Escape($oldDemoMarker))).Count
$countLF = ([regex]::Matches($content, [regex]::Escape($oldDemoMarkerLF))).Count

if (($countCRLF + $countLF) -ne 1) {
    throw "Could not uniquely identify the old demo Analytics block. No changes made."
}

$marker = if ($countCRLF -eq 1) { $oldDemoMarker } else { $oldDemoMarkerLF }
$start = $content.IndexOf($marker)

if ($start -lt 0) {
    throw "Could not locate the duplicate block. No changes made."
}

$endMarker = '    return (' 
$end = $content.IndexOf($endMarker, $start + $marker.Length)

if ($end -lt 0) {
    throw "Could not locate the next renderContent return. No changes made."
}

$demoBlock = $content.Substring($start, $end - $start)

if ($demoBlock -notmatch 'Illustrative monthly employee and attrition activity') {
    throw "The identified block does not match the expected demo Analytics section. No changes made."
}

if (Test-Path $backup) {
    throw "Backup file already exists: $backup. No changes made."
}

Copy-Item -Path $path -Destination $backup

$content = $content.Remove($start, $end - $start)

$content = $content.Replace(
    ': ${predictions.average_predicted_risk_percentage}%',
    ': `${predictions.average_predicted_risk_percentage}%`'
)

Set-Content -Path $path -Value $content -Encoding utf8 -NoNewline

Write-Host "Duplicate demo Analytics block removed."
Write-Host "Average risk percentage JSX expression corrected."
Write-Host "Backup saved to: $backup"
