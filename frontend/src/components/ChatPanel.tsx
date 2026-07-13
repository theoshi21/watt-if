import React, { useCallback, useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { createChatMessage, getChatHistory, streamQuestion, clearChatHistory } from '../api/client'
import { useAuth } from '../context/AuthContext'

interface Message {
  id: number
  role: 'user' | 'assistant' | 'error'
  text: string
}

export const ChatPanel: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [waiting, setWaiting] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(true)
  const [historyError, setHistoryError] = useState<string | null>(null)
  const streamingMsgId = useRef<number | null>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const nextId = useRef(0)
  const { user } = useAuth()

  const scrollToBottom = useCallback(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight
  }, [])

  // Load chat history when user changes (account switch or initial mount)
  useEffect(() => {
    setMessages([])
    setHistoryError(null)
    setHistoryLoading(true)
    nextId.current = 0

    if (!user) { setHistoryLoading(false); return }

    getChatHistory()
      .then((rows) => {
        setMessages(
          rows
            .filter((r) => r.role === 'user' || r.role === 'assistant')
            .map((r) => ({ id: nextId.current++, role: r.role as 'user' | 'assistant', text: r.text }))
        )
      })
      .catch((err) => {
        setHistoryError(err instanceof Error ? err.message : 'Could not load chat history.')
      })
      .finally(() => setHistoryLoading(false))
  }, [user?.id])

  useEffect(() => { scrollToBottom() }, [messages, waiting, historyLoading, scrollToBottom])

  useEffect(() => {
    const el = listRef.current
    if (!el) return
    const observer = new ResizeObserver(() => scrollToBottom())
    observer.observe(el)
    return () => observer.disconnect()
  }, [scrollToBottom])

  const append = (role: Message['role'], text: string): number => {
    const id = nextId.current++
    setMessages((prev) => [...prev, { id, role, text }])
    return id
  }

  const updateMessage = (id: number, text: string) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, text } : m)))
  }

  const handleClear = async () => {
    if (loading) return
    try {
      await clearChatHistory()
    } catch {
      // best-effort — clear the UI regardless
    }
    setMessages([])
    setInput('')
    inputRef.current?.focus()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const q = input.trim()
    if (!q) return
    setInput('')
    append('user', q)
    setLoading(true)
    setWaiting(true)

    const assistantId = append('assistant', '')
    streamingMsgId.current = assistantId
    let accumulated = ''
    let streamErrored = false

    try {
      await streamQuestion(
        q,
        (delta) => {
          setWaiting(false)
          accumulated += delta
          updateMessage(assistantId, accumulated)
        },
        (_sources) => {
          streamingMsgId.current = null
          setWaiting(false)
        },
        (errMsg) => {
          streamErrored = true
          streamingMsgId.current = null
          setWaiting(false)
          updateMessage(assistantId, '')
          append('error', `Could not display answer: ${errMsg}`)
        },
      )
    } catch (err) {
      streamErrored = true
      const msg = err instanceof Error ? err.message : 'An error occurred'
      updateMessage(assistantId, '')
      append('error', `Could not display answer: ${msg}`)
    } finally {
      streamingMsgId.current = null
      setWaiting(false)
      setLoading(false)
    }

    if (!streamErrored && accumulated) {
      try { await createChatMessage({ role: 'user', text: q }) } catch { /* ignore */ }
      try { await createChatMessage({ role: 'assistant', text: accumulated }) } catch { /* ignore */ }
    }
  }

  return (
    <section
      className="card"
      aria-label="Chat"
      style={{
        display: 'flex',
        flexDirection: 'column',
        flex: 1,           // fill the AskPage container
        minHeight: 0,      // allow flex child to shrink below content size
        overflow: 'hidden',
      }}
    >
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '0.75rem',
        flexShrink: 0,
      }}>
        <h2 style={{
          margin: 0,
          fontFamily: 'var(--font-sans)',
          fontSize: '1rem',
          fontWeight: 600,
          color: 'var(--color-text-primary)',
        }}>
          Ask about your forecast
        </h2>
        <button
          onClick={handleClear}
          disabled={loading || messages.length === 0}
          title="Clear conversation"
          style={{
            background: 'none',
            border: '1px solid var(--color-border)',
            borderRadius: '0.375rem',
            padding: '0.25rem 0.6rem',
            cursor: messages.length === 0 || loading ? 'not-allowed' : 'pointer',
            color: messages.length === 0 || loading ? 'var(--color-text-muted)' : 'var(--color-text-primary)',
            fontFamily: 'var(--font-sans)',
            fontSize: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.3rem',
            opacity: messages.length === 0 || loading ? 0.45 : 1,
            transition: 'opacity 0.15s',
          }}
          aria-label="Clear conversation"
        >
          {/* Trash icon */}
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
            <path d="M10 11v6M14 11v6" />
            <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
          </svg>
          Clear chat
        </button>
      </div>

      {/* ── Message thread ───────────────────────────────────────────────── */}
      <div
        ref={listRef}
        role="log"
        aria-live="polite"
        aria-label="Conversation"
        style={{
          flex: 1,
          minHeight: 0,           // critical — allows this to shrink in a flex column
          overflowY: 'auto',
          borderRadius: '0.5rem',
          padding: '0.75rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
          background: 'var(--color-page-bg)',
          border: '1px solid var(--color-border)',
        }}
      >
        {historyLoading && (
          <div style={bubbleStyle('assistant')}>
            <BounceDots />
            <span style={{ fontFamily: 'var(--font-sans)', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
              Loading history…
            </span>
          </div>
        )}

        {historyError && !historyLoading && (
          <p style={{ color: 'var(--color-text-muted)', textAlign: 'center', margin: 'auto', fontFamily: 'var(--font-sans)', fontSize: '0.85rem' }}>
            Chat history could not be loaded: {historyError}
          </p>
        )}

        {messages.length === 0 && !loading && !historyLoading && (
          <div style={{ margin: 'auto', textAlign: 'center', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <p style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-sans)', fontSize: '0.9rem', margin: 0 }}>
              Ask a question about your electricity forecast.
            </p>
            <p style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-sans)', fontSize: '0.8rem', margin: 0 }}>
              e.g. "What will my bill be next month?"
            </p>
          </div>
        )}

        {messages.map((m) => {
          // Hide the empty assistant placeholder while waiting for the first token
          if (m.role === 'assistant' && m.text === '' && streamingMsgId.current === m.id) {
            return null
          }
          return (
            <div key={m.id} role="article" aria-label={m.role} style={bubbleStyle(m.role)}>
              {m.role === 'assistant' ? (
                streamingMsgId.current === m.id ? (
                  <span style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--font-sans)', fontSize: '0.9rem' }}>{m.text}</span>
                ) : (
                  <ReactMarkdown
                    components={{
                      p: ({ children }) => <p style={{ margin: '0 0 0.4rem', fontFamily: 'var(--font-sans)', fontSize: '0.9rem' }}>{children}</p>,
                      ul: ({ children }) => <ul style={{ margin: '0.2rem 0', paddingLeft: '1.2rem' }}>{children}</ul>,
                      li: ({ children }) => <li style={{ marginBottom: '0.2rem', fontFamily: 'var(--font-sans)', fontSize: '0.9rem' }}>{children}</li>,
                      strong: ({ children }) => <strong style={{ color: 'var(--color-text-primary)' }}>{children}</strong>,
                    }}
                  >
                    {m.text}
                  </ReactMarkdown>
                )
              ) : (
                <span style={{ fontFamily: 'var(--font-sans)', fontSize: '0.9rem' }}>{m.text}</span>
              )}
            </div>
          )
        })}

        {waiting && (
          <div style={bubbleStyle('assistant')}>
            <BounceDots />
            <span style={{ fontFamily: 'var(--font-sans)', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
              Generating answer…
            </span>
            <style>{`
              @keyframes bounce {
                0%, 80%, 100% { transform: translateY(0); }
                40% { transform: translateY(-5px); }
              }
            `}</style>
          </div>
        )}
      </div>

      {/* ── Input ────────────────────────────────────────────────────────── */}
      <div style={{ flexShrink: 0, marginTop: '0.75rem' }}>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            ref={inputRef}
            type="text"
            aria-label="Question input"
            placeholder="e.g. What will my bill be next month?"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            maxLength={500}
            disabled={loading}
            style={{
              flex: 1,
              padding: '0.5rem 0.75rem',
              borderRadius: '0.375rem',
              border: '1px solid var(--color-input-border)',
              fontSize: '0.9rem',
              fontFamily: 'var(--font-sans)',
              background: 'var(--color-input-fill)',
              color: 'var(--color-text-primary)',
            }}
          />
          <button
            type="submit"
            disabled={loading || historyLoading || input.trim().length === 0}
            aria-label="Submit question"
            className="btn-primary"
          >
            {loading ? '…' : 'Ask'}
          </button>
        </form>
        <div aria-live="polite" style={{ fontSize: '0.72rem', fontFamily: 'var(--font-sans)', color: 'var(--color-text-muted)', marginTop: '0.25rem', textAlign: 'right' }}>
          {input.length}/500
        </div>
      </div>
    </section>
  )
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function bubbleStyle(role: 'user' | 'assistant' | 'error'): React.CSSProperties {
  return {
    alignSelf: role === 'user' ? 'flex-end' : 'flex-start',
    maxWidth: '85%',
    padding: '0.6rem 0.9rem',
    borderRadius: '0.75rem',
    background:
      role === 'user'      ? 'var(--color-accent-primary)' :
      role === 'error'     ? 'var(--color-rating-poor-bg)' :
                             'var(--color-card-bg)',
    color:
      role === 'user'      ? 'var(--color-text-on-accent)' :
      role === 'error'     ? 'var(--color-red)'           :
                             'var(--color-text-primary)',
    border:
      role === 'assistant' ? '1px solid var(--color-border)' :
      role === 'error'     ? '1px solid var(--color-red)'    :
                             'none',
    boxShadow: '0 1px 3px rgba(0,0,0,0.07)',
    display: 'flex',
    alignItems: 'center',
    gap: '0.4rem',
    flexWrap: 'wrap' as const,
  }
}

function BounceDots() {
  return (
    <span style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}>
      {[0, 1, 2].map((i) => (
        <span key={i} style={{
          width: 7, height: 7, borderRadius: '50%',
          background: 'var(--color-text-muted)',
          display: 'inline-block',
          animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
        }} />
      ))}
    </span>
  )
}
