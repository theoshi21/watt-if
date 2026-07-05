import React, { useRef, useState } from 'react'
import { uploadCsv } from '../api/client'

interface Props {
  onUploadSuccess?: (filename: string) => void
}

type PanelStatus = 'idle' | 'uploading' | 'success' | 'error'

export const UploadPanel: React.FC<Props> = ({ onUploadSuccess }) => {
  const [panelStatus, setPanelStatus] = useState<PanelStatus>('idle')
  const [message, setMessage] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const filename = file.name
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

      setPanelStatus('success')
      setMessage(`✓ ${res.rows_received} row(s) ingested. Click Train Model to update the forecast.`)
      onUploadSuccess?.(filename)
    } catch (err) {
      setPanelStatus('error')
      setMessage(err instanceof Error ? err.message : 'Upload failed.')
    }
  }

  const isbusy = panelStatus === 'uploading'

  const labelText = () => {
    if (panelStatus === 'uploading') return '⬆ Uploading…'
    return 'Choose CSV'
  }

  return (
    <section className="card" aria-label="Upload CSV">
      <h2 style={{
        margin: '0 0 0.2rem',
        fontFamily: 'var(--font-sans)',
        fontSize: '1rem',
        fontWeight: 600,
        color: 'var(--color-text-primary)',
      }}>
        Upload Bill Data
      </h2>
      <p style={{
        margin: '0 0 1rem',
        fontFamily: 'var(--font-sans)',
        fontSize: '0.78rem',
        color: 'var(--color-text-muted)',
      }}>
        Upload a monthly electricity bill CSV. Rate, weather, and ENSO columns are optional.
      </p>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
        <label
          htmlFor="csv-upload"
          className={`btn-primary${isbusy ? ' btn-primary--disabled' : ''}`}
          style={{
            display: 'inline-block',
            cursor: isbusy ? 'not-allowed' : 'pointer',
            whiteSpace: 'nowrap',
            opacity: isbusy ? 0.7 : 1,
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
                panelStatus === 'error' ? 'var(--color-red)' :
                panelStatus === 'success' ? 'var(--color-teal)' : 'var(--color-text-muted)',
            }}
          >
            {message}
          </span>
        )}
      </div>
    </section>
  )
}
