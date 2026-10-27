$ErrorActionPreference = "Stop"

$root = "C:\Users\pasup\OneDrive\Desktop\WorkForce-AI-Pro"
$appFile = Join-Path $root "frontend\src\App.jsx"

if (!(Test-Path $appFile)) {
    throw "App.jsx not found: $appFile"
}

$app = Get-Content $appFile -Raw

$pattern = "(?s)if\s*\(\s*activePage\s*===\s*'Analytics'\s*\)\s*\{.*?(?=\r?\n\s*if\s*\(\s*activePage\s*===|\r?\n\s*return\s*\()"

$matches = [regex]::Matches($app, $pattern)

if ($matches.Count -ne 1) {
    throw "Expected exactly one Analytics section boundary, but found $($matches.Count). No changes saved."
}

$replacement = @"
if (activePage === 'Analytics') {
  const overview = analyticsData?.employee_overview
  const predictions = analyticsData?.prediction_overview
  const hiring = analyticsData?.monthly_hiring || []
  const departments = analyticsData?.department_distribution || []
  const predictionTrend = analyticsData?.monthly_predictions || []
  const riskDistribution = predictions?.risk_distribution || {
    LOW: 0,
    MEDIUM: 0,
    HIGH: 0,
  }

  const departmentColors = ['#6658e8', '#36b8a0', '#f5a84b', '#ef7193', '#5b9bd5']

  return (
    <section className="analytics-page">
      {analyticsLoading && (
        <div className="notice-box">
          <LoaderCircle size={17} />
          Loading live workforce analytics...
        </div>
      )}

      {analyticsError && (
        <div className="notice-box">
          <CircleAlert size={17} />
          {analyticsError}
          <button type="button" onClick={() => void loadAnalyticsData()}>
            Retry
          </button>
        </div>
      )}

      {!analyticsLoading && !analyticsError && analyticsData && (
        <>
          <div className="dashboard-stats">
            <div className="panel">
              <p>Total employees</p>
              <h2>{overview?.total_employees ?? 0}</h2>
            </div>
            <div className="panel">
              <p>Active employees</p>
              <h2>{overview?.active_employees ?? 0}</h2>
            </div>
            <div className="panel">
              <p>Inactive employees</p>
              <h2>{overview?.inactive_employees ?? 0}</h2>
            </div>
            <div className="panel">
              <p>Saved AI predictions</p>
              <h2>{predictions?.total_predictions ?? 0}</h2>
            </div>
          </div>

          <div className="panel chart-panel">
            <div className="panel-heading">
              <div>
                <h2>Monthly hiring</h2>
                <p>Employees grouped by their recorded joining dates.</p>
              </div>
              <CalendarDays size={19} color="#77748c" />
            </div>

            {hiring.length > 0 ? (
              <div className="chart-wrap large-chart">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={hiring}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="label" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="employees_joined"
                      name="Employees joined"
                      stroke="#6658e8"
                      fill="#6658e8"
                      fillOpacity={0.15}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p>No employee joining-date records are available yet.</p>
            )}
          </div>

          <div className="panel chart-panel">
            <div className="panel-heading">
              <div>
                <h2>Department distribution</h2>
                <p>Active employees in each active department.</p>
              </div>
            </div>

            {departments.some((item) => item.active_employees > 0) ? (
              <>
                <div className="chart-wrap pie-wrap">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={departments.filter((item) => item.active_employees > 0)}
                        dataKey="active_employees"
                        nameKey="department"
                        innerRadius={62}
                        outerRadius={92}
                        paddingAngle={4}
                        stroke="none"
                      >
                        {departments
                          .filter((item) => item.active_employees > 0)
                          .map((item, index) => (
                            <Cell
                              key={item.department_id}
                              fill={departmentColors[index % departmentColors.length]}
                            />
                          ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                {departments.map((item, index) => (
                  <div className="legend-row" key={item.department_id}>
                    <span>
                      <i style={{ background: departmentColors[index % departmentColors.length] }} />
                      {item.department}
                    </span>
                    <strong>{item.active_employees}</strong>
                  </div>
                ))}
              </>
            ) : (
              <p>No active department employee records are available yet.</p>
            )}
          </div>

          <div className="panel chart-panel">
            <div className="panel-heading">
              <div>
                <h2>AI prediction activity</h2>
                <p>Saved prediction records, not actual employee resignations.</p>
              </div>
              <BrainCircuit size={19} color="#77748c" />
            </div>

            {predictionTrend.length > 0 ? (
              <div className="chart-wrap large-chart">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={predictionTrend}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="label" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Area
                      type="monotone"
                      dataKey="prediction_count"
                      name="Saved predictions"
                      stroke="#36b8a0"
                      fill="#36b8a0"
                      fillOpacity={0.15}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p>No saved AI prediction records are available yet.</p>
            )}

            <div className="legend-row">
              <span>Low predicted risk</span>
              <strong>{riskDistribution.LOW ?? 0}</strong>
            </div>
            <div className="legend-row">
              <span>Medium predicted risk</span>
              <strong>{riskDistribution.MEDIUM ?? 0}</strong>
            </div>
            <div className="legend-row">
              <span>High predicted risk</span>
              <strong>{riskDistribution.HIGH ?? 0}</strong>
            </div>

            <p>
              Average predicted risk: {predictions?.average_predicted_risk_percentage == null
                ? 'Not available'
                : `${predictions.average_predicted_risk_percentage}%`}
            </p>
          </div>

          <div className="notice-box">
            <CircleAlert size={17} />
            Analytics are aggregated from database records. AI predictions indicate
            predicted risk only; actual attrition cannot be calculated until employee
            exit records are stored.
          </div>
        </>
      )}

      {!analyticsLoading && !analyticsError && !analyticsData && (
        <div className="notice-box">
          <CircleAlert size={17} />
          No analytics data is loaded yet.
          <button type="button" onClick={() => void loadAnalyticsData()}>
            Load analytics
          </button>
        </div>
      )}
    </section>
  )
}
"@

$updated = $app.Substring(0, $matches[0].Index) +
    $replacement +
    $app.Substring($matches[0].Index + $matches[0].Length)

$backupFile = "$appFile.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item $appFile $backupFile
Set-Content -Path $appFile -Value $updated -Encoding utf8

Write-Host ""
Write-Host "Analytics section updated."
Write-Host "Backup: $backupFile"
Write-Host "Updated: $appFile"
