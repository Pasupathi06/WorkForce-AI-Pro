import React, { useEffect, useState } from 'react'
import {
  Shield, RefreshCw, Search, ShieldAlert, CheckCircle2, FileText
} from 'lucide-react'
import { auditLogAPI, getErrorMessage } from '../api'

export default function AuditLogsView({ canManage, user }) {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')

  const loadLogs = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await auditLogAPI.list({ limit: 150 })
      setLogs(res || [])
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadLogs()
  }, [])

  const filteredLogs = search.trim()
    ? logs.filter(
        (l) =>
          l.action?.toLowerCase().includes(search.toLowerCase()) ||
          l.target_type?.toLowerCase().includes(search.toLowerCase()) ||
          l.user_name?.toLowerCase().includes(search.toLowerCase()) ||
          l.details?.toLowerCase().includes(search.toLowerCase())
      )
    : logs

  return (
    <div className="module-container">
      <div className="panel-heading">
        <div>
          <h2>Security & System Audit Trails</h2>
          <p>Chronological record of user authentication, state mutations, and privileged system transactions.</p>
        </div>
        <div className="heading-actions">
          <button className="subtle-button" onClick={loadLogs} disabled={loading}>
            <RefreshCw size={15} /> Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="notice-box error">
          <ShieldAlert size={16} /> {error}
        </div>
      )}

      {/* Audit Log Table */}
      <div className="panel">
        <div className="search-box table-search">
          <Search size={17} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter audit entries by actor, action type, or target..."
          />
        </div>

        <div className="table-wrapper">
          <table className="enterprise-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Target Resource</th>
                <th>Details</th>
                <th>IP Address</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan="6" className="empty-cell">
                    {loading ? 'Loading audit trail...' : 'No audit records match the current filter.'}
                  </td>
                </tr>
              ) : (
                filteredLogs.map((l) => (
                  <tr key={l.id}>
                    <td>{new Date(l.created_at).toLocaleString()}</td>
                    <td><strong>{l.user_name || 'System / Service'}</strong></td>
                    <td><span className="action-pill">{l.action}</span></td>
                    <td><code>{l.target_type} {l.target_id ? `#${l.target_id}` : ''}</code></td>
                    <td><small>{l.details || 'Standard state change'}</small></td>
                    <td><small>{l.ip_address || '127.0.0.1'}</small></td>
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
