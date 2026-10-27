import React, { useEffect, useState } from 'react'
import {
  Award, Star, Plus, RefreshCw, CheckCircle2, ShieldAlert
} from 'lucide-react'
import { performanceAPI, employeeAPI, getErrorMessage } from '../api'

export default function PerformanceView({ canManage, user }) {
  const [reviews, setReviews] = useState([])
  const [summary, setSummary] = useState(null)
  const [employees, setEmployees] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionNotice, setActionNotice] = useState('')

  const [showModal, setShowModal] = useState(false)
  const [formData, setFormData] = useState({
    employee_id: '',
    review_period: 'Q3 2026',
    rating: 4.5,
    goals: '',
    strengths: '',
    improvement_areas: '',
    feedback: '',
  })

  const loadData = async () => {
    setLoading(true)
    setError('')
    try {
      const [rRes, sRes, empRes] = await Promise.all([
        performanceAPI.list({ limit: 100 }),
        performanceAPI.summary(),
        employeeAPI.list({ page_size: 100 }),
      ])
      setReviews(rRes || [])
      setSummary(sRes)
      const empList = empRes?.items || empRes || []
      setEmployees(empList)
      if (empList.length > 0 && !formData.employee_id) {
        setFormData((prev) => ({ ...prev, employee_id: empList[0].id }))
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

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await performanceAPI.create({
        employee_id: Number(formData.employee_id),
        review_period: formData.review_period,
        rating: Number(formData.rating),
        goals: formData.goals,
        strengths: formData.strengths,
        improvement_areas: formData.improvement_areas,
        feedback: formData.feedback,
      })
      setActionNotice('Performance appraisal saved!')
      setShowModal(false)
      loadData()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div className="module-container">
      <div className="panel-heading">
        <div>
          <h2>Performance Appraisal & Reviews</h2>
          <p>Score talent competency, evaluate milestone achievements, and log 360 appraisals.</p>
        </div>
        <div className="heading-actions">
          <button className="subtle-button" onClick={loadData} disabled={loading}>
            <RefreshCw size={15} /> Refresh
          </button>
          {canManage && (
            <button className="primary-button" onClick={() => setShowModal(true)}>
              <Plus size={16} /> New Review
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
          <div className="kpi-label"><Star size={16} /> Org Rating Average</div>
          <div className="kpi-value">{summary?.average_rating ?? 0} / 5.0</div>
          <small className="kpi-sub">Benchmark score</small>
        </div>
        <div className="kpi-card">
          <div className="kpi-label"><Award size={16} /> Top Performers</div>
          <div className="kpi-value success-text">{summary?.top_performers ?? 0}</div>
          <small className="kpi-sub">Rating &gt;= 4.5</small>
        </div>
        <div className="kpi-card">
          <div className="kpi-label"><ShieldAlert size={16} /> Needs Support</div>
          <div className="kpi-value warning-text">{summary?.needs_support ?? 0}</div>
          <small className="kpi-sub">Rating &lt; 3.0</small>
        </div>
        <div className="kpi-card">
          <div className="kpi-label"><CheckCircle2 size={16} /> Completed Appraisals</div>
          <div className="kpi-value">{summary?.total_reviews ?? 0}</div>
          <small className="kpi-sub">Logged review cycles</small>
        </div>
      </div>

      {/* Review History Table */}
      <div className="panel">
        <h3>Appraisal Records</h3>
        <div className="table-wrapper">
          <table className="enterprise-table">
            <thead>
              <tr>
                <th>Period</th>
                <th>Employee</th>
                <th>Rating</th>
                <th>Reviewer</th>
                <th>Strengths</th>
                <th>Improvement Areas</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {reviews.length === 0 ? (
                <tr>
                  <td colSpan="7" className="empty-cell">
                    No performance reviews logged yet. Click "New Review" to evaluate an employee.
                  </td>
                </tr>
              ) : (
                reviews.map((r) => (
                  <tr key={r.id}>
                    <td><strong>{r.review_period}</strong></td>
                    <td>{r.employee_name || `Emp #${r.employee_id}`}</td>
                    <td>
                      <span className="rating-pill">
                        <Star size={13} fill="#f59e0b" color="#f59e0b" /> {r.rating.toFixed(1)}
                      </span>
                    </td>
                    <td>{r.reviewer_name || 'HR Admin'}</td>
                    <td>{r.strengths || 'Consistent deliverable focus'}</td>
                    <td>{r.improvement_areas || 'Cross-team communication'}</td>
                    <td>
                      <span className="status-pill active">
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

      {/* Review Modal */}
      {showModal && (
        <div className="modal-backdrop" onClick={() => setShowModal(false)}>
          <div className="add-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Submit Performance Review</h3>
              <button className="icon-button" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Employee</label>
                <select
                  value={formData.employee_id}
                  onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                  required
                >
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.user?.full_name || emp.employee_code} ({emp.designation})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Review Period</label>
                  <input
                    type="text"
                    required
                    value={formData.review_period}
                    onChange={(e) => setFormData({ ...formData, review_period: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Rating (1.0 to 5.0)</label>
                  <input
                    type="number"
                    min="1.0"
                    max="5.0"
                    step="0.1"
                    required
                    value={formData.rating}
                    onChange={(e) => setFormData({ ...formData, rating: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Key Strengths</label>
                <input
                  type="text"
                  placeholder="e.g. Exceptional problem solving and mentorship"
                  value={formData.strengths}
                  onChange={(e) => setFormData({ ...formData, strengths: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>Areas for Development</label>
                <input
                  type="text"
                  placeholder="e.g. Needs to improve documentation pace"
                  value={formData.improvement_areas}
                  onChange={(e) => setFormData({ ...formData, improvement_areas: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>General Evaluator Feedback</label>
                <textarea
                  placeholder="Detailed observations and appraisal notes..."
                  value={formData.feedback}
                  onChange={(e) => setFormData({ ...formData, feedback: e.target.value })}
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="subtle-button" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="primary-button">
                  Save Evaluation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
