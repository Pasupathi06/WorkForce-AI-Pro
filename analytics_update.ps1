$ErrorActionPreference = "Stop"

$root = "C:\Users\pasup\OneDrive\Desktop\WorkForce-AI-Pro"
$appFile = Join-Path $root "frontend\src\App.jsx"
$apiFile = Join-Path $root "frontend\src\api.js"

if (!(Test-Path $appFile)) {
    throw "App.jsx not found: $appFile"
}

if (!(Test-Path $apiFile)) {
    throw "api.js not found: $apiFile"
}

$app = Get-Content $appFile -Raw
$api = Get-Content $apiFile -Raw

if ($api -notmatch 'export\s+const\s+analyticsAPI\s*=') {
    throw "analyticsAPI missing in api.js. Save analyticsAPI before continuing."
}

if ($app -notmatch '\banalyticsAPI\b') {
    $app = $app.Replace(
        "  attritionAPI,`r`n} from './api'",
        "  attritionAPI,`r`n  analyticsAPI,`r`n} from './api'"
    )
    $app = $app.Replace(
        "  attritionAPI,`n} from './api'",
        "  attritionAPI,`n  analyticsAPI,`n} from './api'"
    )
}

if ($app -notmatch 'const\s+\[analyticsData,\s*setAnalyticsData\]') {
    $anchor = "  const [dashboardData, setDashboardData] = useState({"
    if (!$app.Contains($anchor)) {
        throw "Dashboard state not found. No changes saved."
    }

    $state = @"
  const [analyticsData, setAnalyticsData] = useState(null)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)
  const [analyticsError, setAnalyticsError] = useState('')

"@
    $app = $app.Replace($anchor, $state + $anchor)
}

if ($app -notmatch 'async function loadAnalyticsData\s*\(') {
    $anchor = "  async function loadDashboardData() {"
    if (!$app.Contains($anchor)) {
        throw "Dashboard function not found. No changes saved."
    }

    $fn = @"
  async function loadAnalyticsData() {
    if (!canManage) {
      setAnalyticsData(null)
      setAnalyticsError('HR or Admin access is required.')
      setAnalyticsLoading(false)
      return
    }

    setAnalyticsLoading(true)
    setAnalyticsError('')

    try {
      const response = await analyticsAPI.overview()
      setAnalyticsData(response)
    } catch (error) {
      setAnalyticsData(null)
      setAnalyticsError(
        getErrorMessage(error) || 'Unable to load workforce analytics.'
      )
    } finally {
      setAnalyticsLoading(false)
    }
  }

"@
    $app = $app.Replace($anchor, $fn + $anchor)
}

if ($app -notmatch "activePage\s*!==\s*'Analytics'") {
    $anchor = @"
  useEffect(() => {
    if (!authenticated || !canManage || activePage !== 'Departments') return
    loadDepartments()
  }, [authenticated, canManage, activePage])
"@

    if (!$app.Contains($anchor)) {
        throw "Departments effect not found. No changes saved."
    }

    $effect = @"

  useEffect(() => {
    if (!authenticated || !canManage || activePage !== 'Analytics') return
    void loadAnalyticsData()
  }, [authenticated, canManage, activePage])
"@
    $app = $app.Replace($anchor, $anchor + $effect)
}

$backupFile = "$appFile.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
Copy-Item $appFile $backupFile
Set-Content -Path $appFile -Value $app -Encoding utf8

Write-Host ""
Write-Host "Analytics integration steps 1-4 saved."
Write-Host "Backup: $backupFile"
Write-Host "Updated: $appFile"
