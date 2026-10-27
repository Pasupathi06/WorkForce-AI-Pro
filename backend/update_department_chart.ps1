$ErrorActionPreference = "Stop"

$path = (Resolve-Path "..\frontend\src\App.jsx").Path
$content = [System.IO.File]::ReadAllText($path)

$start = '<h2>Department distribution</h2>'
$end = '{demoDepartmentData.map((item) => ('

$startIndex = $content.IndexOf($start)
if ($startIndex -lt 0) { throw "Department chart start not found. No changes made." }

$endIndex = $content.IndexOf($end, $startIndex)
if ($endIndex -lt 0) { throw "Department chart legend not found. No changes made." }

$closing = '))}'
$endIndex = $content.IndexOf($closing, $endIndex)
if ($endIndex -lt 0) { throw "Department chart legend end not found. No changes made." }
$endIndex += $closing.Length

$replacement = @"
<h2>Department distribution</h2>
            <p>Active employee count by department.</p>

            {dashboardData.loading ? (
              <p>Loading department data...</p>
            ) : dashboardData.departments.length === 0 ? (
              <p>{dashboardData.error || "No department data is available yet."}</p>
            ) : (
              <>
                <div className="chart-wrap pie-wrap">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={dashboardData.departments.filter((item) => item.value !== null && item.value > 0)}
                        dataKey="value"
                        nameKey="name"
                        innerRadius={62}
                        outerRadius={92}
                        paddingAngle={4}
                        stroke="none"
                      >
                        {dashboardData.departments
                          .filter((item) => item.value !== null && item.value > 0)
                          .map((item) => (
                            <Cell key={item.id} fill={item.color} />
                          ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                {dashboardData.departments.map((item) => (
                  <div className="legend-row" key={item.id}>
                    <span><i style={{ background: item.color }} />{item.name}</span>
                    <strong>{item.value === null ? "Unavailable" : item.value.toLocaleString()}</strong>
                  </div>
                ))}
              </>
            )}
"@

$updated = $content.Substring(0, $startIndex) + $replacement + $content.Substring($endIndex)

Copy-Item -LiteralPath $path -Destination "$path.department-chart-backup" -Force
[System.IO.File]::WriteAllText($path, $updated, [System.Text.UTF8Encoding]::new($false))

Write-Host "Department chart updated. Backup created." -ForegroundColor Green
