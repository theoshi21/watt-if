/**
 * Typed API client for the WATT-IF FastAPI backend.
 * All requests target http://localhost:8000 (configurable via VITE_API_BASE).
 */

import type {
  AskResponse,
  ForecastResponse,
  HealthResponse,
  Horizon,
  ModelInfoResponse,
  UploadResponse,
} from './types'

const BASE_URL = (import.meta as Record<string, unknown> & { env?: Record<string, string> })
  .env?.VITE_API_BASE ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, init)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const detail = (body as { detail?: string }).detail ?? res.statusText
    throw new Error(`${res.status}: ${detail}`)
  }
  return res.json() as Promise<T>
}

/** POST /upload — submit a CSV file for ingestion */
export async function uploadCsv(file: File): Promise<UploadResponse> {
  const form = new FormData()
  form.append('file', file)
  return request<UploadResponse>('/upload', { method: 'POST', body: form })
}

/** POST /forecast — request a SARIMAX forecast */
export async function getForecast(horizon: Horizon): Promise<ForecastResponse> {
  return request<ForecastResponse>('/forecast', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ horizon }),
  })
}

/** POST /ask — submit a natural-language question (streaming SSE) */
export async function streamQuestion(
  question: string,
  onToken: (delta: string) => void,
  onDone: (sources: AskResponse['sources']) => void,
  onError: (message: string) => void,
): Promise<void> {
  const res = await fetch(`${BASE_URL}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const detail = (body as { detail?: string }).detail ?? res.statusText
    onError(`${res.status}: ${detail}`)
    return
  }

  const reader = res.body?.getReader()
  if (!reader) {
    onError('No response body from server.')
    return
  }

  const decoder = new TextDecoder()
  let buffer = ''

  let doneCalled = false

  while (true) {
    const { done, value } = await reader.read()
    if (done) {
      // Stream closed — ensure onDone is called even if the SSE done event
      // was missed (e.g. network buffer didn't flush the last line).
      if (!doneCalled) onDone([])
      break
    }

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    // Keep last (potentially incomplete) line in buffer
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const event = JSON.parse(line.slice(6)) as {
          type: 'token' | 'done' | 'error'
          text?: string
          sources?: AskResponse['sources']
        }
        if (event.type === 'token' && event.text) {
          onToken(event.text)
        } else if (event.type === 'done') {
          doneCalled = true
          onDone(event.sources ?? [])
        } else if (event.type === 'error') {
          doneCalled = true
          onError(event.text ?? 'An error occurred.')
        }
      } catch {
        // malformed line — skip
      }
    }
  }
}

/** GET /health — probe backend subsystems */
export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}

/** GET /model-info — fetch model evaluation metrics */
export async function getModelInfo(): Promise<ModelInfoResponse> {
  return request<ModelInfoResponse>('/model-info')
}

/** GET /status — check background training state */
export async function getTrainingStatus(): Promise<{ status: string; error: string | null }> {
  return request<{ status: string; error: string | null }>('/status')
}
