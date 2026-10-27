import React, { useEffect, useRef, useState } from 'react'
import { Bell, CheckCheck, CircleAlert, Sparkles, X } from 'lucide-react'
import { notificationAPI } from '../api'

export default function NotificationBell({ user }) {
  const [unreadCount, setUnreadCount] = useState(0)
  const [notifications, setNotifications] = useState([])
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef(null)

  const fetchUnread = async () => {
    try {
      const res = await notificationAPI.unreadCount()
      setUnreadCount(res?.unread_count || 0)
    } catch {
      // silently fallback
    }
  }

  const fetchList = async () => {
    try {
      const res = await notificationAPI.list({ limit: 20 })
      setNotifications(res || [])
    } catch {
      // silently fallback
    }
  }

  useEffect(() => {
    fetchUnread()
    const timer = setInterval(fetchUnread, 30000)
    return () => clearInterval(timer)
  }, [])

  const toggleDropdown = () => {
    if (!isOpen) {
      fetchList()
      fetchUnread()
    }
    setIsOpen(!isOpen)
  }

  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleOutsideClick)
    }
    return () => document.removeEventListener('mousedown', handleOutsideClick)
  }, [isOpen])

  const handleMarkRead = async (id) => {
    try {
      await notificationAPI.markRead(id)
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      )
      fetchUnread()
    } catch {
      // ignore
    }
  }

  const handleMarkAllRead = async () => {
    try {
      await notificationAPI.markAllRead()
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })))
      setUnreadCount(0)
    } catch {
      // ignore
    }
  }

  return (
    <div className="notification-bell-container" ref={dropdownRef}>
      <button
        className="icon-button notification-trigger"
        onClick={toggleDropdown}
        aria-label="Notifications"
      >
        <Bell size={18} />
        {unreadCount > 0 && (
          <span className="notification-badge">{unreadCount > 9 ? '9+' : unreadCount}</span>
        )}
      </button>

      {isOpen && (
        <div className="notification-dropdown">
          <div className="notification-dropdown-header">
            <div>
              <strong>Notifications & Alerts</strong>
              <small>{unreadCount} unread alert(s)</small>
            </div>
            {notifications.some((n) => !n.is_read) && (
              <button className="mark-all-btn" onClick={handleMarkAllRead}>
                <CheckCheck size={14} /> Mark all read
              </button>
            )}
          </div>

          <div className="notification-list">
            {notifications.length === 0 ? (
              <div className="empty-notif">
                <Sparkles size={24} opacity={0.4} />
                <p>No new notifications right now.</p>
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`notif-item ${!n.is_read ? 'unread' : ''}`}
                  onClick={() => !n.is_read && handleMarkRead(n.id)}
                >
                  <div className="notif-item-top">
                    <span className={`priority-tag ${n.priority.toLowerCase()}`}>
                      {n.priority}
                    </span>
                    <small>{new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</small>
                  </div>
                  <strong>{n.title}</strong>
                  <p>{n.message}</p>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
