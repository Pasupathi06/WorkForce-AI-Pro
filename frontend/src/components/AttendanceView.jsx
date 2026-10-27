import React, { useEffect, useState } from 'react'
import {
  Clock, CheckCircle2, AlertCircle, RefreshCw, LogIn, LogOut,
  Calendar, UserCheck, ShieldAlert
} from 'lucide-react'
import { attendanceAPI, employeeAPI, getErrorMessage } from '../api'

export default function AttendanceView({ canManage, user }) {
  const [summary, setSummary] = useState(null)
  const [records, setRecords] = useState([])
  const [shifts, setShifts] = useState([])
  const [employees, setEmployees] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionNotice, setActionNotice] = useState('')

  const [selectedEmployeeId, setSelectedEmployeeId] = useState('')
  const [selectedShiftId, setSelectedShiftId] = useState('')
  const [punchNotes, setPunchNotes] = useState('')

  const loadData = async () => {
    setLoading(true)
    setError('')
    try {
      const [sumRes, recRes, shiftRes, empRes] = await Promise.all([
        attendanceAPI.summary(),
        attendanceAPI.list({ limit: 50 }),
        attendanceAPI.getShifts(),
        employeeAPI.list({ page_size: 100 }),
      ])
      setSummary(sumRes)
      setRecords(recRes || [])
      setShifts(shiftRes || [])
      const empList = empRes?.items || empRes || []
      setEmployees(empList)
      if (empList.length > 0 && !selectedEmployeeId) {
        setSelectedEmployeeId(empList[0].id)
      }
      if (shiftRes && shiftRes.length > 0 && !selectedShiftId) {
        setSelectedShiftId(shiftRes[0].id)
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

  const handleClockIn = async () => {
    if (!selectedEmployeeId) return
    try {
      await attendanceAPI.clockIn({
        employee_id: Number(selectedEmployeeId),
        shift_id: selectedShiftId ? Number(selectedShiftId) : null,
        notes: punchNotes,
      })
      setActionNotice('Clock-in recorded successfully!')
      setPunchNotes('')
      loadData()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const handleClockOut = async () => {
    if (!selectedEmployeeId) return
    try {
      await attendanceAPI.clockOut({
        employee_id: Number(selectedEmployeeId),
        notes: punchNotes,
      })
      setActionNotice('Clock-out recorded and hours calculated!')
      setPunchNotes('')
      loadData()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div className="module-container">
      <div className="panel-heading">
        <div>
          <h2>Attendance & Shift Management</h2>
          <p>Real-time employee punch clocks, shift schedules, and working hours analytics.</p>
        </div>
        <div className="heading-actions">
          <button className="subtle-button" onClick={loadData} disabled={loading}>
            <RefreshCw size={15} /> Refresh
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

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label"><UserCheck size={16} /> Present Today</div>
          <div className="kpi-value">{summary?.present ?? 0}</div>
          <small className="kpi-sub">Total staff: {summary?.total_employees ?? 0}</small>
        </div>
        <div className="kpi-card">
          <div className="kpi-label"><AlertCircle size={16} /> Late Arrivals</div>
          <div className="kpi-value warning-text">{summary?.late ?? 0}</div>
          <small className="kpi-sub">Post-grace period</small>
        </div>
        <div className="kpi-card">
          <div className="kpi-label"><Clock size={16} /> Absent / Off</div>
          <div className="kpi-value error-text">{summary?.absent ?? 0}</div>
          <small className="kpi-sub">Pending check-in</small>
        </div>
        <div className="kpi-card">
          <div className="kpi-label"><CheckCircle2 size={16} /> Attendance Rate</div>
          <div className="kpi-value">{summary?.attendance_rate ?? 0}%</div>
          <small className="kpi-sub">Today's active ratio</small>
        </div>
      </div>

      {/* Clock-In / Clock-Out Action Console */}
      <div className="panel action-console">
        <h3><Clock size={18} /> Daily Punch Terminal</h3>
        <p>Record employee punch timestamps with automated shift allocation.</p>
        <div className="console-form">
          <div className="form-group">
            <label>Select Employee</label>
            <select
              value={selectedEmployeeId}
              onChange={(e) => setSelectedEmployeeId(e.target.value)}
            >
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.user?.full_name || emp.employee_code} ({emp.employee_code})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Work Shift</label>
            <select
              value={selectedShiftId}
              onChange={(e) => setSelectedShiftId(e.target.value)}
            >
              {shifts.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.start_time} - {s.end_time})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Notes / Remote Punch</label>
            <input
              type="text"
              placeholder="e.g. Work from home / On-site client"
              value={punchNotes}
              onChange={(e) => setPunchNotes(e.target.value)}
            />
          </div>

          <div className="console-buttons">
            <button className="primary-button" onClick={handleClockIn}>
              <LogIn size={16} /> Clock In
            </button>
            <button className="secondary-button" onClick={handleClockOut}>
              <LogOut size={16} /> Clock Out
            </button>
          </div>
        </div>
      </div>

      {/* Attendance History Table */}
      <div className="panel">
        <h3><Calendar size={18} /> Attendance Records</h3>
        <div className="table-wrapper">
          <table className="enterprise-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Employee</th>
                <th>Shift</th>
                <th>Check In</th>
                <th>Check Out</th>
                <th>Hours</th>
                <th>Overtime</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {records.length === 0 ? (
                <tr>
                  <td colSpan="8" className="empty-cell">
                    No attendance records logged yet today. Use the terminal above to clock in.
                  </td>
                </tr>
              ) : (
                records.map((r) => (
                  <tr key={r.id}>
                    <td>{r.date}</td>
                    <td><strong>{r.employee_name || `Emp #${r.employee_id}`}</strong></td>
                    <td>{r.shift_name || 'General'}</td>
                    <td>{r.check_in ? new Date(r.check_in).toLocaleTimeString() : '—'}</td>
                    <td>{r.check_out ? new Date(r.check_out).toLocaleTimeString() : '—'}</td>
                    <td>{r.working_hours > 0 ? `${r.working_hours}h` : 'Active'}</td>
                    <td>{r.overtime_hours > 0 ? `+${r.overtime_hours}h` : '0h'}</td>
                    <td>
                      <span className={`status-pill ${r.status.toLowerCase()}`}>
                        {r.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
