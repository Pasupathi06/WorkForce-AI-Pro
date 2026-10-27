$ErrorActionPreference = "Stop"

$path = ".\frontend\src\App.jsx"
$backup = ".\frontend\src\App.jsx.employee-count-fix.bak"

if (-not (Test-Path $path)) {
    throw "App.jsx not found."
}

$content = [System.IO.File]::ReadAllText((Resolve-Path $path))

$old = '        // Preserve the last known total if the count request fails.'

$new = @"
        if (requestId === employeeRequestId.current) {
          setEmployeeTotal((employeePage - 1) * EMPLOYEES_PER_PAGE + records.length)
        }
"@.TrimEnd()

if (-not $content.Contains($old)) {
    throw "Expected old code not found. No changes made."
}

if (-not (Test-Path $backup)) {
    Copy-Item $path $backup
}

$content = $content.Replace($old, $new)

$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Resolve-Path $path), $content, $encoding)

Write-Host "`n[SUCCESS] Count fallback changed." -ForegroundColor Green
Write-Host "[INFO] Build/tests were not run." -ForegroundColor Yellow

Select-String -Path $path -Pattern "Preserve the last known total|setEmployeeTotal"
