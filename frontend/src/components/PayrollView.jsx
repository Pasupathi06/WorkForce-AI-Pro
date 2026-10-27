import React, { useEffect, useState } from 'react'
import {
  DollarSign, CheckCircle2, RefreshCw, Plus, FileText, ShieldAlert,
  CreditCard, ArrowDownRight, ArrowUpRight
} from 'lucide-react'
import { payrollAPI, employeeAPI, getErrorMessage } from '../api'

export default function PayrollView({ canManage, user }) {
  const [payrolls, setPayrolls] = useState([])
  const [summary, setSummary] = useState(null)
  const [employees, setEmployees] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionNotice, setActionNotice] = useState('')

  const [showGenModal, setShowGenModal] = useState(false)
  const [genData, setGenData] = useState({
    employee_id: '',
    month: '2026-10',
    allowances: 0,
    bonus: 0,
    deductions: 0,
    notes: '',
  })

  const loadData = async () => {
    setLoading(true)
    setError('')
    try {
      const [pRes, sRes, empRes] = await Promise.all([
        payrollAPI.list({ limit: 100 }),
        payrollAPI.summary(),
        employeeAPI.list({ page_size: 100 }),
      ])
      setPayrolls(pRes || [])
      setSummary(sRes)
      const empList = empRes?.items || empRes || []
      setEmployees(empList)
      if (empList.length > 0 && !genData.employee_id) {
        setGenData((prev) => ({ ...prev, employee_id: empList[0].id }))
      }
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleGenerate = async (e) => {
    e.preventDefault()
    try {
      await payrollAPI.generate({
        employee_id: Number(genData.employee_id),
        month: genData.month,
        allowances: Number(genData.allowances),
        bonus: Number(genData.bonus),
        deductions: Number(genData.deductions),
        notes: genData.notes,
      })
      setActionNotice('Payroll generated successfully!')
      setShowGenModal(false)
      loadData()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const handleStatusChange = async (payrollId, status) => {
    try {
      await payrollAPI.updateStatus(payrollId, { status })
      setActionNotice(`Payroll updated to ${status}!`)
      loadData()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div className="module-container">
      <div className="panel-heading">
        <div>
          <h2>Payroll & Compensation Management</h2>
          <p>Automated salary generation, tax deductions, incentives, and payslip disbursement.</p>
        </div>
        <div className="heading-actions">
          <button className="subtle-button" onClick={loadData} disabled={loading}>
            <RefreshCw size={15} /> Refresh
          </button>
          {canManage && (
            <button className="primary-button" onClick={() => setShowGenModal(true)}>
              <Plus size={16} /> Generate Payroll
            </button>
          )}
        </div>
      </div>

      {actionNotice && (
        <div className="notice-box success">
          <CheckCircle2 size={16} /> {actionNotice}
        </div>
      )}

      {error && (
        <div className="notice-box error">
          <ShieldAlert size={16} /> {error}
        </div>
      )}

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label"><DollarSign size={16} /> Net Disbursement</div>
          <div className="kpi-value">${summary?.total_disbursed?.toLocaleString() ?? 0}</div>
          <small className="kpi-sub">Total payroll expenses</small>
        </div>
        <div className="kpi-card">
          <div className="kpi-label"><ArrowDownRight size={16} /> Tax Withholding</div>
          <div className="kpi-value">${summary?.total_tax_deducted?.toLocaleString() ?? 0}</div>
          <small className="kpi-sub">Standard statutory tax</small>
        </div>
        <div className="kpi-card">
          <div className="kpi-label"><ArrowUpRight size={16} /> Bonuses & Incentives</div>
          <div className="kpi-value">${summary?.total_bonuses?.toLocaleString() ?? 0}</div>
          <small className="kpi-sub">Performance bonuses</small>
        </div>
        <div className="kpi-card">
          <div className="kpi-label"><CreditCard size={16} /> Records Status</div>
          <div className="kpi-value">{summary?.paid_count ?? 0} Paid</div>
          <small className="kpi-sub">{summary?.draft_count ?? 0} draft / {summary?.processed_count ?? 0} processed</small>
        </div>
      </div>

      {/* Payroll Table */}
      <div className="panel">
        <h3><FileText size={18} /> Payroll Ledger</h3>
        <div className="table-wrapper">
          <table className="enterprise-table">
            <thead>
              <tr>
                <th>Period</th>
                <th>Employee</th>
                <th>Department</th>
                <th>Basic Salary</th>
                <th>Allowances</th>
                <th>Bonuses</th>
                <th>Tax</th>
                <th>Net Pay</th>
                <th>Status</th>
                {canManage && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {payrolls.length === 0 ? (
                <tr>
                  <td colSpan={canManage ? 10 : 9} className="empty-cell">
                    No payroll records generated yet. Click "Generate Payroll" to create one.
                  </td>
                </tr>
              ) : (
                payrolls.map((p) => (
                  <tr key={p.id}>
                    <td><strong>{p.month}</strong></td>
                    <td>{p.employee_name || p.employee_code}</td>
                    <td>{p.department_name || '—'}</td>
                    <td>${Number(p.basic_salary).toLocaleString()}</td>
                    <td>+${Number(p.allowances).toLocaleString()}</td>
                    <td>+${Number(p.bonus).toLocaleString()}</td>
                    <td className="warning-text">-${Number(p.tax).toLocaleString()}</td>
                    <td><strong className="success-text">${Number(p.net_salary).toLocaleString()}</strong></td>
                    <td>
                      <span className={`status-pill ${p.status.toLowerCase()}`}>
                        {p.status}
                      </span>
                    </td>
                    {canManage && (
                      <td>
                        <div className="table-action-btns">
                          {p.status === 'DRAFT' && (
                            <button
                              className="subtle-button"
                              onClick={() => handleStatusChange(p.id, 'PROCESSED')}
                            >
                              Process
                            </button>
                          )}
                          {p.status === 'PROCESSED' && (
                            <button
                              className="approve-btn"
                              onClick={() => handleStatusChange(p.id, 'PAID')}
                            >
                              Mark Paid
                            </button>
                          )}
                          {p.status === 'PAID' && (
                            <small className="subtle-text">Disbursed</small>
                          )}
                        </div>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Generate Payroll Modal */}
      {showGenModal && (
        <div className="modal-backdrop" onClick={() => setShowGenModal(false)}>
          <div className="add-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Generate Monthly Payroll</h3>
              <button className="icon-button" onClick={() => setShowGenModal(false)}>✕</button>
            </div>
            <form onSubmit={handleGenerate}>
              <div className="form-group">
                <label>Employee</label>
                <select
                  value={genData.employee_id}
                  onChange={(e) => setGenData({ ...genData, employee_id: e.target.value })}
                  required
                >
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.user?.full_name || emp.employee_code} (${emp.salary}/mo)
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Payroll Period (YYYY-MM)</label>
                <input
                  type="month"
                  required
                  value={genData.month}
                  onChange={(e) => setGenData({ ...genData, month: e.target.value })}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Allowances ($)</label>
                  <input
                    type="number"
                    min="0"
                    step="50"
                    value={genData.allowances}
                    onChange={(e) => setGenData({ ...genData, allowances: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Performance Bonus ($)</label>
                  <input
                    type="number"
                    min="0"
                    step="50"
                    value={genData.bonus}
                    onChange={(e) => setGenData({ ...genData, bonus: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Custom Deductions ($)</label>
                <input
                  type="number"
                  min="0"
                  step="50"
                  value={genData.deductions}
                  onChange={(e) => setGenData({ ...genData, deductions: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>Notes / Payslip Remarks</label>
                <input
                  type="text"
                  placeholder="e.g. Standard monthly distribution"
                  value={genData.notes}
                  onChange={(e) => setGenData({ ...genData, notes: e.target.value })}
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="subtle-button" onClick={() => setShowGenModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="primary-button">
                  Compute & Create Payroll
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
