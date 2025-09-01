import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from './api/controller'

export default function App() {
  const [userId, setUserId] = useState(() =>
    localStorage.getItem('userId') || `user-${Math.random().toString(36).slice(2, 8)}`
  )
  const [threadId, setThreadId] = useState(() => localStorage.getItem('threadId'))
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState([])
  const listRef = useRef(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [threads, setThreads] = useState([])
  const [loadingThreads, setLoadingThreads] = useState(false)
  const [editingThread, setEditingThread] = useState(null)
  const [editValue, setEditValue] = useState('')

  useEffect(() => {
    localStorage.setItem('userId', userId)
  }, [userId])

  useEffect(() => {
    if (threadId) localStorage.setItem('threadId', threadId)
  }, [threadId])

  useEffect(() => {
    listRef.current?.lastElementChild?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Base URL is managed in src/api/config.js via VITE_API_BASE_URL
  useMemo(() => null, [])

  async function loadThreads() {
    if (!userId) return
    setLoadingThreads(true)
    try {
      const res = await api.listThreads({ userId })
      // API uses ok() envelope => { success, data }
      const items = Array.isArray(res?.data) ? res.data : res
      setThreads(items || [])
    } catch (err) {
      // Surface minimal error as a system message
      setMessages((m) => [
        ...m,
        { role: 'assistant', text: `Could not load threads: ${err?.message || 'Unknown error'}` },
      ])
    } finally {
      setLoadingThreads(false)
    }
  }

  const handleRenameThread = async (e, thread) => {
    e.stopPropagation()
    const threadId = thread.thread_id || thread.id
    const currentLabel = thread.thread_label || thread.title || ''
    setEditingThread(threadId)
    setEditValue(currentLabel)
  }

  const saveThreadRename = async (e, thread) => {
    e.stopPropagation()
    const threadId = thread.thread_id || thread.id
    try {
      await api.renameThreadLabel({
        userId,
        threadId,
        label: editValue.trim()
      })
      
      // Refresh the thread list
      await loadThreads()
    } catch (err) {
      console.error('Error renaming thread:', err)
      setMessages(m => [...m, { role: 'assistant', text: `Error renaming thread: ${err.message}` }])
    } finally {
      setEditingThread(null)
      setEditValue('')
    }
  }

  const handleKeyDown = (e, thread) => {
    if (e.key === 'Enter') {
      saveThreadRename(e, thread)
    } else if (e.key === 'Escape') {
      setEditingThread(null)
      setEditValue('')
    }
  }

  // Auto-load threads when userId changes
  useEffect(() => {
    if (userId) loadThreads()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId])

  function onSelectThread(id) {
    // Clear messages when selecting a different thread
    if (id !== threadId) {
      setMessages([])
    }
    setThreadId(id || null)
  }

  async function onDeleteThread(id) {
    if (!id) return
    try {
      await api.deleteThread({ userId, threadId: id })
      // If current selected, clear it
      if (threadId === id) setThreadId(null)
      await loadThreads()
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: 'assistant', text: `Delete failed: ${err?.message || 'Unknown error'}` },
      ])
    }
  }

  async function sendMessage(e) {
    e?.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    setMessages((m) => [...m, { role: 'user', text }])
    setInput('')
    setLoading(true)

    try {
      const data = await api.chat({ userId, threadId, message: text })
      const newThreadId = data.threadId || data.thread_id
      if (newThreadId && newThreadId !== threadId) setThreadId(newThreadId)

      setMessages((m) => [...m, { role: 'assistant', text: data.response }])
      // Refresh the thread list after successful chat
      await loadThreads()
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: 'assistant', text: `Error: ${err?.message || 'Unknown error'}` },
      ])
    } finally {
      setLoading(false)
    }
  }

  function clearThread() {
    setThreadId(null)
    localStorage.removeItem('threadId')
    setMessages([])
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="left">
          <button
            className="icon-btn"
            onClick={() => setSidebarOpen((s) => !s)}
            aria-label="Toggle sidebar"
            aria-pressed={sidebarOpen}
            title="Toggle sidebar"
          >
            {sidebarOpen ? (
              <svg className="icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            ) : (
              <svg className="icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="3" y1="6" x2="21" y2="6"></line>
                <line x1="3" y1="12" x2="21" y2="12"></line>
                <line x1="3" y1="18" x2="21" y2="18"></line>
              </svg>
            )}
          </button>
          <h1>AgenticAI</h1>
        </div>
        <div className="controls">
          <label className="userId">
            <span>User ID</span>
            <input
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="user-123"
            />
          </label>
          <button className="secondary" onClick={loadThreads} title="Load threads">Load Threads</button>
          <button className="secondary" onClick={clearThread} title="Start a new thread">
            New Thread
          </button>
        </div>
      </header>

      <div className={`layout ${sidebarOpen ? '' : 'collapsed'}`}>
        <aside className={`sidebar ${sidebarOpen ? '' : 'hidden'}`}>
            <div className="sidebar-header">
              <div className="title">Your Threads</div>
              <div className="actions">
                {loadingThreads ? <span className="muted">Loading…</span> : null}
              </div>
            </div>
            <div className="thread-list">
              {threads?.length ? (
                threads.map((t) => (
                  <div
                    key={t.thread_id || t.id || JSON.stringify(t)}
                    className={`thread-item ${
                      (t.thread_id || t.id) === threadId ? 'active' : ''
                    }`}
                    onClick={() => onSelectThread(t.thread_id || t.id)}
                  >
                    {editingThread === (t.thread_id || t.id) ? (
                      <input
                        type="text"
                        className="thread-edit-input"
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        onKeyDown={(e) => handleKeyDown(e, t)}
                        onBlur={(e) => saveThreadRename(e, t)}
                        autoFocus
                        onClick={(e) => e.stopPropagation()}
                      />
                    ) : (
                      <div 
                        className="thread-title"
                        onDoubleClick={(e) => handleRenameThread(e, t)}
                      >
                        {t.thread_label || t.title || t.thread_id || t.id}
                      </div>
                    )}
                    <button
                      className="thread-delete"
                      title="Delete thread"
                      onClick={(e) => {
                        e.stopPropagation()
                        onDeleteThread(t.thread_id || t.id)
                      }}
                    >
                      ×
                    </button>
                  </div>
                ))
              ) : (
                <div className="empty">No threads found</div>
              )}
            </div>
          </aside>

        <main className="chat">
          <div className="meta">
            <div className="thread-title-display">
              {threads.find(t => (t.thread_id || t.id) === threadId)?.thread_label || 'New Chat'}
            </div>
          </div>
          <div className="messages" ref={listRef}>
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}> 
              <div className="bubble">{m.text}</div>
            </div>
          ))}
          {loading && (
            <div className="msg assistant">
              <div className="bubble typing">Thinking…</div>
            </div>
          )}
          </div>
          <form className="composer" onSubmit={sendMessage}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask something…"
            />
            <button disabled={loading || !input.trim()} type="submit">
              Send
            </button>
          </form>
        </main>
      </div>

      <footer className="footer">FastAPI at <code>http://localhost:8000</code> | UI via Vite</footer>
    </div>
  )
}
