$ErrorActionPreference = "Stop"

$path = "..\frontend\src\App.jsx"
$content = [System.IO.File]::ReadAllText((Resolve-Path $path))

$anchor = "  async function loadDashboardData() {"

$addition = @"
  async function loadDashboardRiskData() {
    if (!canManage) {
      setDashboardRiskEmployees([])
      setDashboardRiskError('HR or Admin access is required.')
      return
    }

    setDashboardRiskLoading(true)
    setDashboardRiskError('')

    try {
      const [employeeResponse, historyResponse] = await Promise.all([
        employeeAPI.list({ page: 1, page_size: 100, active_only: true }),
        attritionAPI.history({ page: 1, page_size: 100 }),
      ])

      const employeeRecords = normalizeList(employeeResponse)
      const historyRecords = normalizeList(historyResponse)
      const latestByEmployee = new Map()

      historyRecords
        .filter((record) => record.employee_id != null)
        .sort((a, b) =>
          new Date(b.created_at || 0).getTime() -
          new Date(a.created_at || 0).getTime()
        )
        .forEach((record) => {
          const id = String(record.employee_id)
          if (!latestByEmployee.has(id)) latestByEmployee.set(id, record)
        })

      setDashboardRiskEmployees(employeeRecords.map((employee, index) => {
        const prediction = latestByEmployee.get(String(employee.id))
        const rawScore = prediction
          ? Number(prediction.attrition_risk_percentage ?? prediction.attrition_probability)
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

if (-not $content.Contains($anchor)) {
    throw "Function anchor not found. No changes made."
}

if ($content.Contains("async function loadDashboardRiskData()")) {
    throw "Risk loading function already exists. No changes made."
}

$stateAnchor = "const [employees, setEmployees] = useState(initialEmployees)"
$stateAddition = @"
const [dashboardRiskEmployees, setDashboardRiskEmployees] = useState([])
const [dashboardRiskLoading, setDashboardRiskLoading] = useState(false)
const [dashboardRiskError, setDashboardRiskError] = useState('')
"@

if (-not $content.Contains($stateAnchor)) {
    throw "Employee state anchor not found. No changes made."
}

$content = $content.Replace($stateAnchor, "$stateAddition`r`n    $stateAnchor")
$content = $content.Replace($anchor, "$addition$anchor")

[System.IO.File]::WriteAllText(
    (Resolve-Path $path),
    $content,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Host "Dashboard risk data loader added." -ForegroundColor Green
