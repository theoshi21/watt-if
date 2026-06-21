import React, { useRef, useState, useEffect } from 'react'
import { uploadCsv, getTrainingStatus } from '../api/client'

interface Props {
  onUploadSuccess?: () => void
}

type PanelStatus = 'idle' | 'uploading' | 'training' | 'success' | 'error'

export const UploadPanel: React.FC<Props> = ({ onUploadSuccess }) => {
  const [panelStatus, setPanelStatus] = useState<PanelStatus>('idle')
  const [message, setMessage] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Clean up polling on unmount
  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current) }, [])

  const stopPolling = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
  }

  const startPolling = (rows: number, onDone: () => void, onFailed: (err: string) => void) => {
    pollRef.current = setInterval(async () => {
      try {
        const s = await getTrainingStatus()
        if (s.status === 'done') {
          stopPolling()
          onDone()
        } else if (s.status === 'failed') {
          stopPolling()
          onFailed(s.error ?? 'Training failed.')
        }
        // keep polling while status === 'running'
      } catch {
        // network hiccup — keep polling
      }
    }, 3000)
  }

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (inputRef.current) inputRef.current.value = ''

    setPanelStatus('uploading')
    setMessage('Uploading data…')

    try {
      const res = await uploadCsv(file)

      if (res.validation_status !== 'ok') {
        setPanelStatus('error')
        setMessage('Validation error — check your CSV columns and format.')
        return
      }

      // Upload done — now wait for background training
      setPanelStatus('training')
      setMessage(`${res.rows_received} row(s) ingested. Training model… (~60 seconds)`)

      startPolling(
        res.rows_received,
        () => {
          setPanelStatus('success')
          setMessage(`✓ ${res.rows_received} row(s) ingested. Model trained — forecast ready.`)
          onUploadSuccess?.()
        },
        (err) => {
          setPanelStatus('error')
          setMessage(`Training failed: ${err}`)
        }
      )
    } catch (err) {
      setPanelStatus('error')
      setMessage(err instanceof Error ? err.message : 'Upload failed.')
    }
  }

  const isbusy = panelStatus === 'uploading' || panelStatus === 'training'

  const labelText = () => {
    if (panelStatus === 'uploading') return '⬆ Uploading…'
    if (panelStatus === 'training') return '⚙ Training…'
    return 'Choose CSV'
  }

  return (
    <section aria-label="Upload CSV">
      <h2 style={{ margin: '0 0 0.5rem' }}>Upload Bill Data</h2>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
        <label
          htmlFor="csv-upload"
          style={{
            display: 'inline-block',
            padding: '0.5rem 1rem',
            background: isbusy ? '#aaa' : '#4f8ef7',
            color: '#fff',
            borderRadius: '4px',
            cursor: isbusy ? 'not-allowed' : 'pointer',
            fontSize: '0.9rem',
            whiteSpace: 'nowrap',
          }}
        >
          <span role={isbusy ? 'status' : undefined}>{labelText()}</span>
        </label>

        <input
          id="csv-upload"
          ref={inputRef}
          type="file"
          accept=".csv"
          disabled={isbusy}
          onChange={handleChange}
          style={{ display: 'none' }}
          aria-label="Upload CSV file"
        />

        {message && (
          <span
            role={panelStatus === 'error' ? 'alert' : 'status'}
            aria-live={panelStatus === 'error' ? 'assertive' : 'polite'}
            style={{
              fontSize: '0.9rem',
              color:
                panelStatus === 'error' ? '#c62828' :
                panelStatus === 'success' ? '#2e7d32' : '#555',
            }}
          >
            {message}
          </span>
        )}
      </div>
    </section>
  )
}
