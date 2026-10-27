import React, { useEffect, useState } from 'react'
import {
  FileSpreadsheet, Download, RefreshCw, BarChart2, CheckCircle2, ShieldAlert
} from 'lucide-react'
import { reportAPI, getErrorMessage } from '../api'

export default function ReportsView({ canManage, user }) {
  const [workforceRep, setWorkforceRep] = useState(null)
  const [attendanceRep, setAttendanceRep] = useState(null)
  const [payrollRep, setPayrollRep] = useState(null)
  const [attritionRep, setAttritionRep] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadReports = async () => {
    setLoading(true)
    setError('')
    try {
      const [w, a, p, att] = await Promise.all([
        reportAPI.workforce(),
        reportAPI.attendance(),
        reportAPI.payroll(),
        reportAPI.attrition(),
      ])
      setWorkforceRep(w)
      setAttendanceRep(a)
      setPayrollRep(p)
      setAttritionRep(att)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadReports()
  }, [])

  const downloadJSON = (data, filename) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${filename}_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="module-container">
      <div className="panel-heading">
        <div>
          <h2>Enterprise Reports & Data Export</h2>
          <p>Download structured audit reports, compliance summaries, and operational analytics.</p>
        </div>
        <div className="heading-actions">
          <button className="subtle-button" onClick={loadReports} disabled={loading}>
            <RefreshCw size={15} /> Refresh Reports
          </button>
        </div>
      </div>

      {error && (
        <div className="notice-box error">
          <ShieldAlert size={16} /> {error}
        </div>
      )}

      <div className="report-card-grid">
        {/* Workforce Report */}
        <div className="panel report-box">
          <div className="report-box-header">
            <h4>Workforce Demographics Report</h4>
            <button
              className="primary-button small-btn"
              onClick={() => downloadJSON(workforceRep, 'workforce_report')}
            >
              <Download size={14} /> Export JSON
            </button>
          </div>
          <p>Headcount breakdown, departmental distributions, and employment statuses.</p>
          {workforceRep && (
            <div className="report-stats-list">
              <div className="stat-line">
                <span>Total Active Headcount</span>
                <strong>{workforceRep.active_employees} staff</strong>
              </div>
              <div className="stat-line">
                <span>Total Departments</span>
                <strong>{workforceRep.departments?.length || 0} departments</strong>
              </div>
              <div className="stat-line">
                <span>Inactive / Exited Records</span>
                <strong>{workforceRep.inactive_employees} staff</strong>
              </div>
            </div>
          )}
        </div>

        {/* Attendance Report */}
        <div className="panel report-box">
          <div className="report-box-header">
            <h4>Attendance & Overtime Audit</h4>
            <button
              className="primary-button small-btn"
              onClick={() => downloadJSON(attendanceRep, 'attendance_report')}
            >
              <Download size={14} /> Export JSON
            </button>
          </div>
          <p>Punctuality rates, cumulative hours worked, and overtime tracking logs.</p>
          {attendanceRep && (
            <div className="report-stats-list">
              <div className="stat-line">
                <span>Total Shift Punches</span>
                <strong>{attendanceRep.total_attendance_records} logs</strong>
              </div>
              <div className="stat-line">
                <span>Cumulative Hours</span>
                <strong>{attendanceRep.total_hours_worked} hrs</strong>
              </div>
              <div className="stat-line">
                <span>Total Overtime Logged</span>
                <strong>+{attendanceRep.total_overtime_hours} hrs</strong>
              </div>
              <div className="stat-line">
                <span>Late Arrival Incidents</span>
                <strong className="warning-text">{attendanceRep.total_late_arrivals}</strong>
              </div>
            </div>
          )}
        </div>

        {/* Payroll Report */}
        <div className="panel report-box">
          <div className="report-box-header">
            <h4>Financial Payroll & Tax Report</h4>
            <button
              className="primary-button small-btn"
              onClick={() => downloadJSON(payrollRep, 'payroll_report')}
            >
              <Download size={14} /> Export JSON
            </button>
          </div>
          <p>Compensation payouts, statutory tax deductions, and performance incentives.</p>
          {payrollRep && (
            <div className="report-stats-list">
              <div className="stat-line">
                <span>Net Salary Disbursed</span>
                <strong className="success-text">${payrollRep.total_net_expenditure?.toLocaleString()}</strong>
              </div>
              <div className="stat-line">
                <span>Statutory Tax Withholding</span>
                <strong>${payrollRep.total_tax_deducted?.toLocaleString()}</strong>
              </div>
              <div className="stat-line">
                <span>Incentives & Bonuses</span>
                <strong>${payrollRep.total_bonuses_paid?.toLocaleString()}</strong>
              </div>
              <div className="stat-line">
                <span>Average Compensation</span>
                <strong>${payrollRep.average_net_salary?.toLocaleString()}</strong>
              </div>
            </div>
          )}
        </div>

        {/* Attrition Report */}
        <div className="panel report-box">
          <div className="report-box-header">
            <h4>AI Flight Risk & Retention Report</h4>
            <button
              className="primary-button small-btn"
              onClick={() => downloadJSON(attritionRep, 'attrition_report')}
            >
              <Download size={14} /> Export JSON
            </button>
          </div>
          <p>Machine learning risk score distributions and predictive intervention logs.</p>
          {attritionRep && (
            <div className="report-stats-list">
              <div className="stat-line">
                <span>Model Inferences Evaluated</span>
                <strong>{attritionRep.total_predictions} runs</strong>
              </div>
              <div className="stat-line">
                <span>Critical Risk (&gt;70%)</span>
                <strong className="error-text">{attritionRep.high_risk_count}</strong>
              </div>
              <div className="stat-line">
                <span>Moderate Risk (40-70%)</span>
                <strong className="warning-text">{attritionRep.medium_risk_count}</strong>
              </div>
              <div className="stat-line">
                <span>Stable Retention (&lt;40%)</span>
                <strong className="success-text">{attritionRep.low_risk_count}</strong>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
