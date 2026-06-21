import React, { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { streamQuestion } from '../api/client'

interface Message {
  id: number
  role: 'user' | 'assistant' | 'error'
  text: string
}

export const ChatPanel: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [waiting, setWaiting] = useState(false)  // true until first token arrives
  const streamingMsgId = useRef<number | null>(null)  // id of the bubble being streamed into
  const listRef = useRef<HTMLDivElement>(null)
  const nextId = useRef(0)

  const scrollToBottom = () => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight
    }
  }

  // Scroll when messages array changes (new message added or removed)
  useEffect(() => {
    scrollToBottom()
  }, [messages, waiting])

  // Also scroll whenever the container's height changes — catches every token
  // that makes the assistant bubble taller, firing after the browser paints.
  useEffect(() => {
    const el = listRef.current
    if (!el) return
    const observer = new ResizeObserver(() => scrollToBottom())
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  const append = (role: Message['role'], text: string): number => {
    const id = nextId.current++
    setMessages((prev) => [...prev, { id, role, text }])
    return id
  }

  const updateMessage = (id: number, text: string) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, text } : m))
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const q = input.trim()
    if (!q) return
    setInput('')
    append('user', q)
    setLoading(true)
    setWaiting(true)

    // Create the assistant bubble immediately so tokens stream into it
    const assistantId = append('assistant', '')
    streamingMsgId.current = assistantId
    let accumulated = ''

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
          streamingMsgId.current = null
          setWaiting(false)
          updateMessage(assistantId, '')
          append('error', `Could not display answer: ${errMsg}`)
        },
      )
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'An error occurred'
      updateMessage(assistantId, '')
      append('error', `Could not display answer: ${msg}`)
    } finally {
      streamingMsgId.current = null
      setWaiting(false)
      setLoading(false)
    }
  }

  return (
    <section aria-label="Chat" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <h2 style={{ margin: '0 0 0.5rem' }}>Ask about your forecast</h2>

      {/* Message thread */}
      <div
        ref={listRef}
        role="log"
        aria-live="polite"
        aria-label="Conversation"
        style={{
          flex: 1,
          overflowY: 'auto',
          border: '1px solid #ddd',
          borderRadius: '6px',
          padding: '0.75rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
          minHeight: '200px',
          maxHeight: '420px',
          background: '#fafafa',
        }}
      >
        {messages.length === 0 && !loading && (
          <p style={{ color: '#aaa', textAlign: 'center', margin: 'auto', fontSize: '0.9rem' }}>
            Ask a question about your electricity forecast.<br />
            <span style={{ fontSize: '0.8rem' }}>
              e.g. "What will my bill be in January 2025?"
            </span>
          </p>
        )}

        {messages.map((m) => (
          <div
            key={m.id}
            role="article"
            aria-label={m.role}
            style={{
              alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '85%',
              padding: '0.6rem 0.9rem',
              borderRadius: '10px',
              background:
                m.role === 'user' ? '#3a7bd5' :
                m.role === 'error' ? '#ffebee' : '#ffffff',
              color:
                m.role === 'user' ? '#fff' :
                m.role === 'error' ? '#c62828' : '#222',
              fontSize: '0.9rem',
              lineHeight: 1.6,
              boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
              border: m.role === 'assistant' ? '1px solid #e8e8e8' : 'none',
            }}
          >
            {m.role === 'assistant' ? (
              /* Only render markdown once streaming is complete — mid-stream
                 incomplete markers (e.g. unclosed **) render as raw text otherwise */
              streamingMsgId.current === m.id ? (
                <span style={{ whiteSpace: 'pre-wrap' }}>{m.text}</span>
              ) : (
                <ReactMarkdown
                  components={{
                    p: ({ children }) => <p style={{ margin: '0 0 0.4rem' }}>{children}</p>,
                    ul: ({ children }) => <ul style={{ margin: '0.2rem 0', paddingLeft: '1.2rem' }}>{children}</ul>,
                    li: ({ children }) => <li style={{ marginBottom: '0.2rem' }}>{children}</li>,
                    strong: ({ children }) => <strong style={{ color: '#1a1a2e' }}>{children}</strong>,
                  }}
                >
                  {m.text}
                </ReactMarkdown>
              )
            ) : (
              m.text
            )}
          </div>
        ))}

        {/* "Generating answer…" indicator — shown until first token arrives */}
        {waiting && (
          <div
            aria-label="Generating answer"
            style={{
              alignSelf: 'flex-start',
              padding: '0.6rem 0.9rem',
              borderRadius: '10px',
              background: '#ffffff',
              border: '1px solid #e8e8e8',
              color: '#888',
              fontSize: '0.85rem',
              boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}
          >
            <span style={{ display: 'inline-flex', gap: 4 }}>
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  style={{
                    width: 7,
                    height: 7,
                    borderRadius: '50%',
                    background: '#aaa',
                    animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite`,
                  }}
                />
              ))}
            </span>
            Generating answer…
            <style>{`
              @keyframes bounce {
                0%, 80%, 100% { transform: translateY(0); }
                40% { transform: translateY(-5px); }
              }
            `}</style>
          </div>
        )}

      </div>

      {/* Input form */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
        <input
          type="text"
          aria-label="Question input"
          placeholder="e.g. What will my bill be in January 2025?"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          maxLength={500}
          disabled={loading}
          style={{
            flex: 1,
            padding: '0.5rem 0.75rem',
            borderRadius: '6px',
            border: '1px solid #ccc',
            fontSize: '0.9rem',
          }}
        />
        <button
          type="submit"
          disabled={loading || input.trim().length === 0}
          aria-label="Submit question"
          style={{
            padding: '0.5rem 1.1rem',
            borderRadius: '6px',
            background: loading ? '#aaa' : '#3a7bd5',
            color: '#fff',
            border: 'none',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontWeight: 500,
          }}
        >
          {loading ? '…' : 'Ask'}
        </button>
      </form>
      <div aria-live="polite" style={{ fontSize: '0.75rem', color: '#aaa', marginTop: '0.25rem' }}>
        {input.length}/500
      </div>
    </section>
  )
}
