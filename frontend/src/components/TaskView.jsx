import React, { useEffect, useState } from 'react'
import {
  CheckSquare, Plus, RefreshCw, Clock, CheckCircle2, AlertTriangle, ShieldAlert
} from 'lucide-react'
import { taskAPI, employeeAPI, getErrorMessage } from '../api'

export default function TaskView({ canManage, user }) {
  const [tasks, setTasks] = useState([])
  const [employees, setEmployees] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionNotice, setActionNotice] = useState('')

  const [showModal, setShowModal] = useState(false)
  const [taskData, setTaskData] = useState({
    title: '',
    description: '',
    assigned_to_id: '',
    priority: 'MEDIUM',
    due_date: '',
  })

  const loadData = async () => {
    setLoading(true)
    setError('')
    try {
      const [tRes, empRes] = await Promise.all([
        taskAPI.list({ limit: 100 }),
        employeeAPI.list({ page_size: 100 }),
      ])
      setTasks(tRes || [])
      const empList = empRes?.items || empRes || []
      setEmployees(empList)
      if (empList.length > 0 && !taskData.assigned_to_id) {
        setTaskData((prev) => ({ ...prev, assigned_to_id: empList[0].id }))
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

  const handleCreate = async (e) => {
    e.preventDefault()
    try {
      await taskAPI.create({
        title: taskData.title,
        description: taskData.description,
        assigned_to_id: Number(taskData.assigned_to_id),
        priority: taskData.priority,
        due_date: taskData.due_date || null,
      })
      setActionNotice('Task assigned successfully!')
      setShowModal(false)
      setTaskData({
        title: '',
        description: '',
        assigned_to_id: employees[0]?.id || '',
        priority: 'MEDIUM',
        due_date: '',
      })
      loadData()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const handleStatusChange = async (taskId, newStatus) => {
    try {
      await taskAPI.update(taskId, { status: newStatus })
      setActionNotice(`Task status updated to ${newStatus}!`)
      loadData()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const handleDelete = async (taskId) => {
    if (!window.confirm('Delete this task?')) return
    try {
      await taskAPI.delete(taskId)
      setActionNotice('Task deleted!')
      loadData()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const pendingTasks = tasks.filter((t) => t.status === 'PENDING')
  const inProgressTasks = tasks.filter((t) => t.status === 'IN_PROGRESS')
  const completedTasks = tasks.filter((t) => t.status === 'COMPLETED')

  return (
    <div className="module-container">
      <div className="panel-heading">
        <div>
          <h2>Workflow & Task Management</h2>
          <p>Organize team deliverables, track execution stages, and meet milestone deadlines.</p>
        </div>
        <div className="heading-actions">
          <button className="subtle-button" onClick={loadData} disabled={loading}>
            <RefreshCw size={15} /> Refresh
          </button>
          <button className="primary-button" onClick={() => setShowModal(true)}>
            <Plus size={16} /> New Task
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

      {/* Kanban Columns */}
      <div className="kanban-grid">
        {/* Pending Column */}
        <div className="kanban-column">
          <div className="column-header">
            <h4><Clock size={16} /> Pending ({pendingTasks.length})</h4>
          </div>
          <div className="task-list">
            {pendingTasks.map((t) => (
              <div key={t.id} className="task-card">
                <div className="task-card-header">
                  <span className={`priority-badge ${t.priority.toLowerCase()}`}>
                    {t.priority}
                  </span>
                  <small>{t.due_date || 'No due date'}</small>
                </div>
                <h5>{t.title}</h5>
                {t.description && <p>{t.description}</p>}
                <div className="task-footer">
                  <small>👤 {t.assigned_to_name}</small>
                  <button
                    className="action-link"
                    onClick={() => handleStatusChange(t.id, 'IN_PROGRESS')}
                  >
                    Start →
                  </button>
                </div>
              </div>
            ))}
            {pendingTasks.length === 0 && <div className="empty-sub">No pending tasks</div>}
          </div>
        </div>

        {/* In Progress Column */}
        <div className="kanban-column">
          <div className="column-header">
            <h4><AlertTriangle size={16} /> In Progress ({inProgressTasks.length})</h4>
          </div>
          <div className="task-list">
            {inProgressTasks.map((t) => (
              <div key={t.id} className="task-card in-progress">
                <div className="task-card-header">
                  <span className={`priority-badge ${t.priority.toLowerCase()}`}>
                    {t.priority}
                  </span>
                  <small>{t.due_date || 'No due date'}</small>
                </div>
                <h5>{t.title}</h5>
                {t.description && <p>{t.description}</p>}
                <div className="task-footer">
                  <small>👤 {t.assigned_to_name}</small>
                  <button
                    className="action-link success"
                    onClick={() => handleStatusChange(t.id, 'COMPLETED')}
                  >
                    Complete ✓
                  </button>
                </div>
              </div>
            ))}
            {inProgressTasks.length === 0 && <div className="empty-sub">No tasks in progress</div>}
          </div>
        </div>

        {/* Completed Column */}
        <div className="kanban-column">
          <div className="column-header">
            <h4><CheckCircle2 size={16} /> Completed ({completedTasks.length})</h4>
          </div>
          <div className="task-list">
            {completedTasks.map((t) => (
              <div key={t.id} className="task-card completed">
                <div className="task-card-header">
                  <span className="priority-badge done">Done</span>
                  {canManage && (
                    <button className="del-btn" onClick={() => handleDelete(t.id)}>✕</button>
                  )}
                </div>
                <h5>{t.title}</h5>
                <div className="task-footer">
                  <small>👤 {t.assigned_to_name}</small>
                  <span className="completed-check">✓ Finished</span>
                </div>
              </div>
            ))}
            {completedTasks.length === 0 && <div className="empty-sub">No completed tasks yet</div>}
          </div>
        </div>
      </div>

      {/* Create Task Modal */}
      {showModal && (
        <div className="modal-backdrop" onClick={() => setShowModal(false)}>
          <div className="add-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Assign New Task</h3>
              <button className="icon-button" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Task Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Complete Q4 compliance audit"
                  value={taskData.title}
                  onChange={(e) => setTaskData({ ...taskData, title: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>Assign To Employee</label>
                <select
                  value={taskData.assigned_to_id}
                  onChange={(e) => setTaskData({ ...taskData, assigned_to_id: e.target.value })}
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
                  <label>Priority</label>
                  <select
                    value={taskData.priority}
                    onChange={(e) => setTaskData({ ...taskData, priority: e.target.value })}
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                    <option value="URGENT">Urgent</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Due Date</label>
                  <input
                    type="date"
                    value={taskData.due_date}
                    onChange={(e) => setTaskData({ ...taskData, due_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Description & Scope</label>
                <textarea
                  placeholder="Instructions or acceptance criteria..."
                  value={taskData.description}
                  onChange={(e) => setTaskData({ ...taskData, description: e.target.value })}
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="subtle-button" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="primary-button">
                  Assign Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
