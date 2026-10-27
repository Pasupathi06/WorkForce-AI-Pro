import React, { useEffect, useState } from 'react'
import {
  CalendarDays, CheckCircle2, XCircle, Clock, Plus, RefreshCw, ShieldAlert
} from 'lucide-react'
import { leaveAPI, employeeAPI, getErrorMessage } from '../api'

export default function LeaveView({ canManage, user }) {
  const [leaves, setLeaves] = useState([])
  const [employees, setEmployees] = useState([])
  const [balance, setBalance] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionNotice, setActionNotice] = useState('')

  const [showApplyModal, setShowApplyModal] = useState(false)
  const [applyData, setApplyData] = useState({
    employee_id: '',
    leave_type: 'CASUAL',
    start_date: '',
    end_date: '',
    days_count: 1,
    reason: '',
  })

  const loadData = async () => {
    setLoading(true)
    setError('')
    try {
      const [leaveRes, empRes] = await Promise.all([
        leaveAPI.list({ limit: 50 }),
        employeeAPI.list({ page_size: 100 }),
      ])
      setLeaves(leaveRes || [])
      const empList = empRes?.items || empRes || []
      setEmployees(empList)
      if (empList.length > 0) {
        if (!applyData.employee_id) {
          setApplyData((prev) => ({ ...prev, employee_id: empList[0].id }))
        }
        const balRes = await leaveAPI.balance(empList[0].id)
        setBalance(balRes)
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

  const handleApply = async (e) => {
    e.preventDefault()
    try {
      await leaveAPI.apply({
        employee_id: Number(applyData.employee_id),
        leave_type: applyData.leave_type,
        start_date: applyData.start_date,
        end_date: applyData.end_date,
        days_count: Number(applyData.days_count),
        reason: applyData.reason,
      })
      setActionNotice('Leave application submitted successfully!')
      setShowApplyModal(false)
      loadData()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const handleStatusChange = async (leaveId, status) => {
    try {
      await leaveAPI.updateStatus(leaveId, { status })
      setActionNotice(`Leave request ${status.toLowerCase()}!`)
      loadData()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div className="module-container">
      <div className="panel-heading">
        <div>
          <h2>Leave Management System</h2>
          <p>Employee leave balances, absence workflows, and manager approvals.</p>
        </div>
        <div className="heading-actions">
          <button className="subtle-button" onClick={loadData} disabled={loading}>
            <RefreshCw size={15} /> Refresh
          </button>
          <button className="primary-button" onClick={() => setShowApplyModal(true)}>
            <Plus size={16} /> Apply Leave
          </button>
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

      {/* Leave Balance Quotas */}
      {balance && (
        <div className="kpi-grid">
          <div className="kpi-card">
            <div className="kpi-label">Casual Leaves</div>
            <div className="kpi-value">{balance.remaining_casual} / {balance.casual_leave}</div>
            <small className="kpi-sub">{balance.used_casual} days consumed</small>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">Sick Leaves</div>
            <div className="kpi-value">{balance.remaining_sick} / {balance.sick_leave}</div>
            <small className="kpi-sub">{balance.used_sick} days consumed</small>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">Annual / Earned Leaves</div>
            <div className="kpi-value">{balance.remaining_annual} / {balance.annual_leave}</div>
            <small className="kpi-sub">{balance.used_annual} days consumed</small>
          </div>
          <div className="kpi-card">
            <div className="kpi-label">Year Policy Quota</div>
            <div className="kpi-value">2026</div>
            <small className="kpi-sub">Standard Enterprise Policy</small>
          </div>
        </div>
      )}

      {/* Leave Applications Table */}
      <div className="panel">
        <h3><CalendarDays size={18} /> Leave Applications</h3>
        <div className="table-wrapper">
          <table className="enterprise-table">
            <thead>
              <tr>
                <th>Employee</th>
                <th>Leave Type</th>
                <th>Duration</th>
                <th>Days</th>
                <th>Reason</th>
                <th>Status</th>
                {canManage && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {leaves.length === 0 ? (
                <tr>
                  <td colSpan={canManage ? 7 : 6} className="empty-cell">
                    No leave requests found. Click "Apply Leave" to submit an application.
                  </td>
                </tr>
              ) : (
                leaves.map((l) => (
                  <tr key={l.id}>
                    <td><strong>{l.employee_name || `Emp #${l.employee_id}`}</strong></td>
                    <td><span className="type-badge">{l.leave_type}</span></td>
                    <td>{l.start_date} to {l.end_date}</td>
                    <td>{l.days_count} day(s)</td>
                    <td>{l.reason}</td>
                    <td>
                      <span className={`status-pill ${l.status.toLowerCase()}`}>
                        {l.status}
                      </span>
                    </td>
                    {canManage && (
                      <td>
                        {l.status === 'PENDING' ? (
                          <div className="table-action-btns">
                            <button
                              className="approve-btn"
                              onClick={() => handleStatusChange(l.id, 'APPROVED')}
                            >
                              <CheckCircle2 size={14} /> Approve
                            </button>
                            <button
                              className="reject-btn"
                              onClick={() => handleStatusChange(l.id, 'REJECTED')}
                            >
                              <XCircle size={14} /> Reject
                            </button>
                          </div>
                        ) : (
                          <small className="subtle-text">Completed</small>
                        )}
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Apply Modal */}
      {showApplyModal && (
        <div className="modal-backdrop" onClick={() => setShowApplyModal(false)}>
          <div className="add-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Apply for Leave</h3>
              <button className="icon-button" onClick={() => setShowApplyModal(false)}>✕</button>
            </div>
            <form onSubmit={handleApply}>
              <div className="form-group">
                <label>Employee</label>
                <select
                  value={applyData.employee_id}
                  onChange={(e) => setApplyData({ ...applyData, employee_id: e.target.value })}
                  required
                >
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.user?.full_name || emp.employee_code} ({emp.employee_code})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Leave Type</label>
                <select
                  value={applyData.leave_type}
                  onChange={(e) => setApplyData({ ...applyData, leave_type: e.target.value })}
                >
                  <option value="CASUAL">Casual Leave</option>
                  <option value="SICK">Sick Leave</option>
                  <option value="ANNUAL">Annual Leave</option>
                  <option value="MATERNITY">Maternity / Paternity</option>
                  <option value="UNPAID">Unpaid Leave</option>
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Start Date</label>
                  <input
                    type="date"
                    required
                    value={applyData.start_date}
                    onChange={(e) => setApplyData({ ...applyData, start_date: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>End Date</label>
                  <input
                    type="date"
                    required
                    value={applyData.end_date}
                    onChange={(e) => setApplyData({ ...applyData, end_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Number of Days</label>
                <input
                  type="number"
                  min="0.5"
                  step="0.5"
                  required
                  value={applyData.days_count}
                  onChange={(e) => setApplyData({ ...applyData, days_count: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>Reason for Leave</label>
                <textarea
                  required
                  placeholder="Provide specific reason..."
                  value={applyData.reason}
                  onChange={(e) => setApplyData({ ...applyData, reason: e.target.value })}
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="subtle-button" onClick={() => setShowApplyModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="primary-button">
                  Submit Application
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
