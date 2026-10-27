import React, { useEffect, useState } from 'react'
import {
  FileText, Upload, Trash2, Download, RefreshCw, CheckCircle2, ShieldAlert
} from 'lucide-react'
import { documentAPI, employeeAPI, getErrorMessage } from '../api'

export default function DocumentView({ canManage, user }) {
  const [documents, setDocuments] = useState([])
  const [employees, setEmployees] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionNotice, setActionNotice] = useState('')

  const [typeFilter, setTypeFilter] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [docData, setDocData] = useState({
    employee_id: '',
    title: '',
    document_type: 'CONTRACT',
    file_name: '',
    file_path: '/uploads/documents/',
    file_size_kb: 240,
  })

  const loadData = async () => {
    setLoading(true)
    setError('')
    try {
      const [dRes, empRes] = await Promise.all([
        documentAPI.list({ limit: 100 }),
        employeeAPI.list({ page_size: 100 }),
      ])
      setDocuments(dRes || [])
      const empList = empRes?.items || empRes || []
      setEmployees(empList)
      if (empList.length > 0 && !docData.employee_id) {
        setDocData((prev) => ({ ...prev, employee_id: empList[0].id }))
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

  const handleUpload = async (e) => {
    e.preventDefault()
    try {
      await documentAPI.upload({
        employee_id: Number(docData.employee_id),
        title: docData.title,
        document_type: docData.document_type,
        file_name: docData.file_name || `${docData.title.toLowerCase().replace(/\s+/g, '_')}.pdf`,
        file_path: `/vault/docs/${docData.document_type.toLowerCase()}/${Date.now()}.pdf`,
        file_size_kb: Number(docData.file_size_kb),
      })
      setActionNotice('Document uploaded and indexed successfully!')
      setShowModal(false)
      loadData()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const handleDelete = async (docId) => {
    if (!window.confirm('Delete this document from the vault?')) return
    try {
      await documentAPI.delete(docId)
      setActionNotice('Document removed from records!')
      loadData()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const filteredDocs = typeFilter
    ? documents.filter((d) => d.document_type === typeFilter)
    : documents

  return (
    <div className="module-container">
      <div className="panel-heading">
        <div>
          <h2>Document Management Vault</h2>
          <p>Secure employee document vault for IDs, employment agreements, and compliance records.</p>
        </div>
        <div className="heading-actions">
          <button className="subtle-button" onClick={loadData} disabled={loading}>
            <RefreshCw size={15} /> Refresh
          </button>
          {canManage && (
            <button className="primary-button" onClick={() => setShowModal(true)}>
              <Upload size={16} /> Upload Document
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

      {/* Filter Tabs */}
      <div className="filter-pill-bar">
        {['', 'CONTRACT', 'ID_PROOF', 'RESUME', 'TAX_FORM', 'CERTIFICATE'].map((type) => (
          <button
            key={type}
            className={`filter-pill ${typeFilter === type ? 'active' : ''}`}
            onClick={() => setTypeFilter(type)}
          >
            {type === '' ? 'All Documents' : type.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Documents Table */}
      <div className="panel">
        <h3><FileText size={18} /> Employee Records & Assets</h3>
        <div className="table-wrapper">
          <table className="enterprise-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Employee</th>
                <th>Category</th>
                <th>File Name</th>
                <th>File Size</th>
                <th>Uploaded At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocs.length === 0 ? (
                <tr>
                  <td colSpan="7" className="empty-cell">
                    No documents found. Click "Upload Document" to add employee files to the vault.
                  </td>
                </tr>
              ) : (
                filteredDocs.map((d) => (
                  <tr key={d.id}>
                    <td><strong>{d.title}</strong></td>
                    <td>{d.employee_name || `Emp #${d.employee_id}`}</td>
                    <td><span className="type-badge">{d.document_type}</span></td>
                    <td><code>{d.file_name}</code></td>
                    <td>{d.file_size_kb > 0 ? `${d.file_size_kb} KB` : '150 KB'}</td>
                    <td>{new Date(d.created_at).toLocaleDateString()}</td>
                    <td>
                      <div className="table-action-btns">
                        <button
                          className="subtle-button"
                          title="Download document"
                          onClick={() => alert(`Downloading ${d.file_name}...`)}
                        >
                          <Download size={14} /> Download
                        </button>
                        {canManage && (
                          <button
                            className="reject-btn"
                            title="Delete file"
                            onClick={() => handleDelete(d.id)}
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Upload Modal */}
      {showModal && (
        <div className="modal-backdrop" onClick={() => setShowModal(false)}>
          <div className="add-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Upload Employee Document</h3>
              <button className="icon-button" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleUpload}>
              <div className="form-group">
                <label>Employee</label>
                <select
                  value={docData.employee_id}
                  onChange={(e) => setDocData({ ...docData, employee_id: e.target.value })}
                  required
                >
                  {employees.map((emp) => (
                    <option key={emp.id} value={emp.id}>
                      {emp.user?.full_name || emp.employee_code} ({emp.designation})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Document Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Employment Contract 2026"
                  value={docData.title}
                  onChange={(e) => setDocData({ ...docData, title: e.target.value })}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Document Category</label>
                  <select
                    value={docData.document_type}
                    onChange={(e) => setDocData({ ...docData, document_type: e.target.value })}
                  >
                    <option value="CONTRACT">Contract Agreement</option>
                    <option value="ID_PROOF">Identity Proof / Passport</option>
                    <option value="RESUME">Resume / Curriculum Vitae</option>
                    <option value="TAX_FORM">Tax Exemption / W-4</option>
                    <option value="CERTIFICATE">Professional Certificate</option>
                    <option value="OTHER">Other Compliance File</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Simulated File Size (KB)</label>
                  <input
                    type="number"
                    min="10"
                    value={docData.file_size_kb}
                    onChange={(e) => setDocData({ ...docData, file_size_kb: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>File Name</label>
                <input
                  type="text"
                  placeholder="e.g. passport_scan.pdf"
                  value={docData.file_name}
                  onChange={(e) => setDocData({ ...docData, file_name: e.target.value })}
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="subtle-button" onClick={() => setShowModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="primary-button">
                  Upload to Vault
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
