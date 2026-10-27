import React, { useEffect, useRef, useState } from 'react'
import {
  MessageSquare, Send, Users, User, RefreshCw, CheckCircle2, ShieldAlert
} from 'lucide-react'
import { chatAPI, getErrorMessage } from '../api'

export default function ChatView({ canManage, user }) {
  const [messages, setMessages] = useState([])
  const [contacts, setContacts] = useState([])
  const [activeChannel, setActiveChannel] = useState('general')
  const [selectedUser, setSelectedUser] = useState(null)
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const messagesEndRef = useRef(null)

  const loadContacts = async () => {
    try {
      const res = await chatAPI.contacts()
      setContacts(res || [])
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  const loadMessages = async () => {
    try {
      const params = selectedUser
        ? { other_user_id: selectedUser.id }
        : { channel: activeChannel }
      const res = await chatAPI.messages(params)
      setMessages(res || [])
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadContacts()
  }, [])

  useEffect(() => {
    loadMessages()
  }, [selectedUser, activeChannel])

  const handleSend = async (e) => {
    e.preventDefault()
    if (!text.trim()) return

    try {
      await chatAPI.send({
        channel: selectedUser ? 'direct' : activeChannel,
        receiver_id: selectedUser ? selectedUser.id : null,
        message: text.trim(),
      })
      setText('')
      loadMessages()
    } catch (err) {
      setError(getErrorMessage(err))
    }
  }

  return (
    <div className="module-container">
      <div className="panel-heading">
        <div>
          <h2>One-to-One Chat & Team Communication</h2>
          <p>Real-time messaging, department collaboration channels, and direct employee communications.</p>
        </div>
        <div className="heading-actions">
          <button className="subtle-button" onClick={loadMessages}>
            <RefreshCw size={15} /> Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="notice-box error">
          <ShieldAlert size={16} /> {error}
        </div>
      )}

      <div className="chat-layout">
        {/* Contacts & Channels Sidebar */}
        <div className="chat-sidebar">
          <h4>Channels</h4>
          <button
            className={`channel-item ${!selectedUser && activeChannel === 'general' ? 'active' : ''}`}
            onClick={() => { setSelectedUser(null); setActiveChannel('general') }}
          >
            <Users size={16} /> # general-workforce
          </button>
          <button
            className={`channel-item ${!selectedUser && activeChannel === 'announcements' ? 'active' : ''}`}
            onClick={() => { setSelectedUser(null); setActiveChannel('announcements') }}
          >
            <MessageSquare size={16} /> # hr-announcements
          </button>

          <h4 style={{ marginTop: '1.5rem' }}>Direct Messages</h4>
          <div className="contacts-list">
            {contacts
              .filter((c) => c.id !== user?.id)
              .map((c) => (
                <button
                  key={c.id}
                  className={`contact-item ${selectedUser?.id === c.id ? 'active' : ''}`}
                  onClick={() => setSelectedUser(c)}
                >
                  <div className="avatar-circle">
                    {c.full_name?.charAt(0) || 'U'}
                  </div>
                  <div className="contact-info">
                    <strong>{c.full_name}</strong>
                    <small>{c.role}</small>
                  </div>
                </button>
              ))}
            {contacts.length <= 1 && (
              <small className="empty-sub">No other colleagues online</small>
            )}
          </div>
        </div>

        {/* Messaging Box */}
        <div className="chat-main">
          <div className="chat-header">
            <h4>
              {selectedUser ? (
                <>💬 Direct with <strong>{selectedUser.full_name}</strong> ({selectedUser.role})</>
              ) : (
                <>📢 Channel: <strong>#{activeChannel}</strong></>
              )}
            </h4>
          </div>

          <div className="chat-messages-scroll">
            {messages.length === 0 ? (
              <div className="chat-empty">
                <MessageSquare size={32} opacity={0.4} />
                <p>No messages yet. Say hello to start the conversation!</p>
              </div>
            ) : (
              messages.map((m) => {
                const isMe = m.sender_id === user?.id
                return (
                  <div key={m.id} className={`chat-bubble-row ${isMe ? 'me' : 'them'}`}>
                    <div className="chat-bubble">
                      <div className="bubble-header">
                        <strong>{isMe ? 'You' : m.sender_name || 'Colleague'}</strong>
                        <small>{new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</small>
                      </div>
                      <p>{m.message}</p>
                    </div>
                  </div>
                )
              })
            )}
            <div ref={messagesEndRef} />
          </div>

          <form className="chat-input-bar" onSubmit={handleSend}>
            <input
              type="text"
              placeholder={selectedUser ? `Message ${selectedUser.full_name}...` : `Message #${activeChannel}...`}
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <button type="submit" className="primary-button" disabled={!text.trim()}>
              <Send size={16} /> Send
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
