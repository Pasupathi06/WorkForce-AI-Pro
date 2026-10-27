$ErrorActionPreference = "Stop"

$path = ".\backend\app\api\routes\employees.py"
$backup = ".\backend\app\api\routes\employees.py.routefix.bak"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " WORKFORCE AI - EMPLOYEE ROUTE FIX" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan

if (-not (Test-Path $path)) {
    Write-Host "[ERROR] Source file not found." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $backup)) {
    Write-Host "[ERROR] Backup file not found. No changes made." -ForegroundColor Red
    exit 1
}

$content = Get-Content $path -Raw

$countPattern = '(?s)@router\.get\(\s*"/\{employee_id\}",\s*response_model=EmployeeResponse,\s*summary="Get employee details",\s*\)\s*@router\.get\(\s*"/count",\s*summary="Count employee records",\s*\)\s*def count_employees\('

if ($content -notmatch $countPattern) {
    Write-Host "[ERROR] Expected count route pattern not found." -ForegroundColor Red
    Write-Host "[INFO] No changes made. Source file needs inspection." -ForegroundColor Yellow
    exit 1
}

$getPattern = '(?m)^def get_employee\('

if ($content -notmatch $getPattern) {
    Write-Host "[ERROR] get_employee function not found. No changes made." -ForegroundColor Red
    exit 1
}

# Remove the misplaced GET /{employee_id} decorator from count_employees.
$content = [regex]::Replace(
    $content,
    $countPattern,
    '@router.get("/count", summary="Count employee records")' + "`r`n" + 'def count_employees(',
    1
)

# Attach GET /{employee_id} to the correct function.
$getDecorator = @(
    '@router.get('
    '    "/{employee_id}",'
    '    response_model=EmployeeResponse,'
    '    summary="Get employee details",'
    ')'
) -join "`r`n"

$content = [regex]::Replace(
    $content,
    $getPattern,
    [System.Text.RegularExpressions.MatchEvaluator]{
        param($match)
        return $getDecorator + "`r`n" + $match.Value
    },
    1
)

# Preserve UTF-8 encoding without a BOM.
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText(
    (Join-Path (Get-Location) $path),
    $content,
    $utf8NoBom
)

Write-Host ""
Write-Host "[SUCCESS] Route decorators updated." -ForegroundColor Green
Write-Host "[BACKUP] Existing backup preserved." -ForegroundColor Cyan
Write-Host "[INFO] Build and tests were not run." -ForegroundColor Yellow

$lines = Get-Content $path
Write-Host ""
Write-Host "===== UPDATED ROUTE DEFINITIONS =====" -ForegroundColor Cyan

for ($i = 212; $i -le 275; $i++) {
    if ($i -lt $lines.Length) {
        "{0,4}: {1}" -f ($i + 1), $lines[$i]
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
