import { useEffect, useMemo, useRef, useState } from 'react'

interface ChatMessage {
  role: 'user' | 'assistant'
  text: string
}

export default function App() {
  const [userId, setUserId] = useState<string>(() =>
    localStorage.getItem('userId') || `user-${Math.random().toString(36).slice(2, 8)}`
  )
  const [threadId, setThreadId] = useState<string | null>(
    () => localStorage.getItem('threadId')
  )
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const listRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    localStorage.setItem('userId', userId)
  }, [userId])

  useEffect(() => {
    if (threadId) localStorage.setItem('threadId', threadId)
  }, [threadId])

  useEffect(() => {
    listRef.current?.lastElementChild?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const baseUrl = useMemo(() => {
    // In dev, Vite proxy forwards /v1 to http://localhost:8000
    return '/v1'
  }, [])

  async function sendMessage(e?: React.FormEvent) {
    e?.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    setMessages((m) => [...m, { role: 'user', text }])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${baseUrl}/agent/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          userId,
          ...(threadId ? { threadId } : {}),
        },
        body: JSON.stringify({ message: text }),
      })

      if (!res.ok) {
        const errText = await res.text()
        throw new Error(`${res.status} ${res.statusText}: ${errText}`)
      }

      const data: {
        threadId: string
        userId: string
        message: string
        response: string
      } = await res.json()

      if (data.threadId && data.threadId !== threadId) setThreadId(data.threadId)

      setMessages((m) => [...m, { role: 'assistant', text: data.response }])
    } catch (err: any) {
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
        <h1>AgenticAI</h1>
        <div className="controls">
          <label className="userId">
            <span>User ID</span>
            <input
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="user-123"
            />
          </label>
          <button className="secondary" onClick={clearThread} title="Start a new thread">
            New Thread
          </button>
        </div>
      </header>

      <main className="chat">
        <div className="meta">
          <div>Thread: {threadId ?? '—'}</div>
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

      <footer className="footer">FastAPI at <code>http://localhost:8000</code> | UI via Vite</footer>
    </div>
  )
}
