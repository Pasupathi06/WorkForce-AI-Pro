$ErrorActionPreference = "Stop"

$path = "..\frontend\src\App.jsx"
$resolvedPath = (Resolve-Path $path).Path
$content = [System.IO.File]::ReadAllText($resolvedPath)

$old = 'employees={initialEmployees.filter((employee) =>'
$new = 'employees={dashboardRiskEmployees.filter((employee) =>'

if (-not $content.Contains($old)) {
    throw "Employee table anchor not found. No changes made."
}

$content = $content.Replace($old, $new)

$oldPlaceholder = "Showing illustrative demo profiles"
$newPlaceholder = "Showing up to 5 active employees from live records."

if (-not $content.Contains($oldPlaceholder)) {
    throw "Dashboard footer anchor not found. No changes made."
}

$content = $content.Replace($oldPlaceholder, $newPlaceholder)

$oldHeading = "placeholder=""Search demo employees..."""
$newHeading = "placeholder=""Search employees..."""

if ($content.Contains($oldHeading)) {
    $content = $content.Replace($oldHeading, $newHeading)
}

$oldDescription = "Illustrative retention profiles"
$newDescription = "Live employee records and latest saved predictions"

if ($content.Contains($oldDescription)) {
    $content = $content.Replace($oldDescription, $newDescription)
}

[System.IO.File]::WriteAllText(
    $resolvedPath,
    $content,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host "Dashboard employee table switched to live data." -ForegroundColor Green
