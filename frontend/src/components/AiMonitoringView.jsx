import React, { useEffect, useState } from 'react'
import {
  BrainCircuit, ShieldAlert, Sparkles, TrendingUp, AlertTriangle, RefreshCw, CheckCircle2
} from 'lucide-react'
import { aiMonitoringAPI, getErrorMessage } from '../api'

export default function AiMonitoringView({ canManage, user }) {
  const [highRiskEmployees, setHighRiskEmployees] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [stabilityData, setStabilityData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadData = async () => {
    setLoading(true)
    setError('')
    try {
      const [riskRes, recRes, stabRes] = await Promise.all([
        aiMonitoringAPI.highRisk(),
        aiMonitoringAPI.recommendations(),
        aiMonitoringAPI.stability(),
      ])
      setHighRiskEmployees(riskRes || [])
      setRecommendations(recRes || [])
      setStabilityData(stabRes)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  return (
    <div className="module-container">
      <div className="panel-heading">
        <div>
          <h2>AI Workforce Monitoring & Decision Support</h2>
          <p>Real-time employee turnover surveillance, early flight risk detection, and prescriptive retention tactics.</p>
        </div>
        <div className="heading-actions">
          <button className="subtle-button" onClick={loadData} disabled={loading}>
            <RefreshCw size={15} /> Refresh AI Feed
          </button>
        </div>
      </div>

      {error && (
        <div className="notice-box error">
          <ShieldAlert size={16} /> {error}
        </div>
      )}

      {/* Stability Metrics */}
      {stabilityData && (
        <div className="kpi-grid">
          <div className="kpi-card">
            <div className="kpi-label"><Sparkles size={16} /> Org Stability Index</div>
            <div className="kpi-value success-text">{stabilityData.overall_stability_score}%</div>
            <small className="kpi-sub">Rating: {stabilityData.stability_rating}</small>
          </div>
          <div className="kpi-card">
            <div className="kpi-label"><TrendingUp size={16} /> 6-Month Retention Forecast</div>
            <div className="kpi-value">94.2%</div>
            <small className="kpi-sub">Projected workforce retention</small>
          </div>
          <div className="kpi-card">
            <div className="kpi-label"><ShieldAlert size={16} /> Monitored High Risk Cases</div>
            <div className="kpi-value warning-text">{highRiskEmployees.length}</div>
            <small className="kpi-sub">Employees flagged by AI engine</small>
          </div>
          <div className="kpi-card">
            <div className="kpi-label"><BrainCircuit size={16} /> Active Interventions</div>
            <div className="kpi-value">{recommendations.length}</div>
            <small className="kpi-sub">Prescriptive strategy blueprints</small>
          </div>
        </div>
      )}

      {/* Real-time High-Risk Radar */}
      <div className="panel">
        <h3><AlertTriangle size={18} color="#ef4444" /> High-Risk Turnover Surveillance</h3>
        <p>Employees flagged by the Scikit-learn attrition model exceeding the 70% flight risk threshold.</p>
        <div className="table-wrapper">
          <table className="enterprise-table">
            <thead>
              <tr>
                <th>Employee</th>
                <th>Department</th>
                <th>Designation</th>
                <th>Attrition Risk</th>
                <th>Model</th>
                <th>Status</th>
                <th>Recommended Action</th>
              </tr>
            </thead>
            <tbody>
              {highRiskEmployees.length === 0 ? (
                <tr>
                  <td colSpan="7" className="empty-cell">
                    No critical flight risk detections at present. All employee profiles are within standard retention boundaries.
                  </td>
                </tr>
              ) : (
                highRiskEmployees.map((e) => (
                  <tr key={e.prediction_id}>
                    <td>
                      <strong>{e.employee_name}</strong>
                      <br /><small>{e.employee_code}</small>
                    </td>
                    <td>{e.department}</td>
                    <td>{e.designation}</td>
                    <td>
                      <span className="risk-badge high">
                        {e.risk_percentage.toFixed(1)}% High Risk
                      </span>
                    </td>
                    <td><small>{e.model_type}</small></td>
                    <td><span className="escalation-tag">Escalated</span></td>
                    <td>
                      <button className="subtle-button" onClick={() => alert(`Initiating retention check for ${e.employee_name}`)}>
                        Schedule 1-on-1 Pulse
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* AI Retention Recommendations */}
      <div className="panel">
        <h3><Sparkles size={18} /> Prescriptive AI Retention Recommendations</h3>
        <p>Targeted policy suggestions calculated to maximize workforce stability and drop voluntary attrition.</p>
        <div className="recommendation-grid">
          {recommendations.map((rec, idx) => (
            <div key={idx} className="rec-card">
              <div className="rec-header">
                <span className={`priority-badge ${rec.priority.toLowerCase()}`}>{rec.priority} PRIORITY</span>
                <span className="rec-category">{rec.category}</span>
              </div>
              <h4>{rec.title}</h4>
              <p>{rec.description}</p>
              <div className="rec-action-box">
                <strong>Action:</strong> {rec.action}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
