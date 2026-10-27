$ErrorActionPreference = "Stop"
$file = (Resolve-Path "..\frontend\src\App.jsx").Path
$content = Get-Content $file -Raw
$start = $content.IndexOf("  async function loadDashboardRiskData()")
$end = $content.IndexOf("  async function loadDashboardData()", $start)

if ($start -lt 0 -or $end -lt 0) {
    throw "Function boundaries not found. No changes made."
}

$replacement = @"
  async function loadDashboardRiskData() {
    if (!canManage) {
      setDashboardRiskEmployees([])
      setDashboardRiskError('HR or Admin access is required.')
      setDashboardRiskLoading(false)
      return
    }

    setDashboardRiskLoading(true)
    setDashboardRiskError('')

    try {
      const pageSize = 100
      const employeeRecords = []
      let employeePage = 1

      while (true) {
        const response = await employeeAPI.list({
          page: employeePage,
          page_size: pageSize,
          active_only: true,
        })
        const records = normalizeList(response)
        employeeRecords.push(...records)
        if (records.length < pageSize) break
        employeePage += 1
      }

      const historyRecords = []
      let historyPage = 1

      while (true) {
        const response = await attritionAPI.history({
          page: historyPage,
          page_size: pageSize,
        })
        const records = normalizeList(response)
        historyRecords.push(...records)
        const total = Number(response?.total)

        if (Number.isFinite(total) && total >= 0) {
          if (historyRecords.length >= total) break
        } else if (records.length < pageSize) {
          break
        }

        if (records.length === 0) break
        historyPage += 1
      }

      const latestByEmployee = new Map()
      historyRecords
        .filter((record) => record.employee_id != null)
        .sort((a, b) => {
          const difference =
            new Date(b.created_at || 0).getTime() -
            new Date(a.created_at || 0).getTime()
          return difference || Number(b.id || 0) - Number(a.id || 0)
        })
        .forEach((record) => {
          const id = String(record.employee_id)
          if (!latestByEmployee.has(id)) latestByEmployee.set(id, record)
        })

      setDashboardRiskEmployees(employeeRecords.map((employee, index) => {
        const prediction = latestByEmployee.get(String(employee.id))
        const rawScore = prediction
          ? Number(prediction.attrition_risk_percentage ??
              (prediction.attrition_probability != null
                ? Number(prediction.attrition_probability) * 100
                : NaN))
          : NaN

        return {
          id: employee.id,
          user_id: employee.user_id,
          name: employee.full_name || employee.employee_code || ('Employee ' + employee.id),
          employee_code: employee.employee_code,
          email: employee.email || '',
          role: employee.designation || 'Designation not set',
          designation: employee.designation || '',
          department: employee.department_name || 'Not assigned',
          department_name: employee.department_name || '',
          department_id: employee.department_id,
          risk: prediction?.risk_level || 'Not calculated',
          score: Number.isFinite(rawScore) ? Math.max(0, Math.min(100, rawScore)) : null,
          initials: getInitials(employee.full_name || employee.employee_code || ('E' + employee.id)),
          color: ['purple', 'blue', 'pink', 'orange', 'green'][index % 5],
          demo: false,
          is_active: employee.is_active,
        }
      }))
    } catch (error) {
      setDashboardRiskEmployees([])
      setDashboardRiskError(
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        'Could not load employee risk data.'
      )
    } finally {
      setDashboardRiskLoading(false)
    }
  }

"@

if ($start -lt 0 -or $end -le $start) {
    throw "Invalid function boundaries."
}

Copy-Item $file "$file.backup-before-risk-pagination" -Force
$updated = $content.Substring(0, $start) + $replacement + $content.Substring($end)
Set-Content -LiteralPath $file -Value $updated -Encoding UTF8 -NoNewline

Write-Host "Dashboard risk pagination function updated." -ForegroundColor Green
