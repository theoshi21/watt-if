/**
 * Typed API client for the WATT-IF FastAPI backend.
 * All requests target http://localhost:8000 (configurable via VITE_API_BASE).
 */

import type {
  AskResponse,
  ChatMessageCreate,
  ChatMessageRow,
  DataEntryCreate,
  DataEntryRow,
  DataEntryUpdate,
  ForecastResponse,
  HealthResponse,
  Horizon,
  MeralcoRateResponse,
  ModelInfoResponse,
  UploadResponse,
} from './types'

const BASE_URL = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

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

/** POST /retrain — manually trigger a full retrain on all available data */
export async function triggerRetrain(): Promise<{ status: string }> {
  return request<{ status: string }>('/retrain', { method: 'POST' })
}

/** DELETE /data/all — permanently wipe all training data and the model artefact */
export async function clearAllData(): Promise<void> {
  const res = await fetch(`${BASE_URL}/data/all`, { method: 'DELETE' })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const detail = (body as { detail?: string }).detail ?? res.statusText
    throw new Error(`${res.status}: ${detail}`)
  }
}

/** GET /data-entries — fetch all data entry log rows ordered by created_at DESC */
export async function getDataEntries(): Promise<DataEntryRow[]> {
  return request<DataEntryRow[]>('/data-entries')
}

/** POST /data-entries — persist a new data entry row */
export async function createDataEntry(entry: DataEntryCreate): Promise<DataEntryRow> {
  return request<DataEntryRow>('/data-entries', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry),
  })
}

/** PUT /data-entries/{id} — update an existing entry */
export async function updateDataEntry(id: number, update: DataEntryUpdate): Promise<DataEntryRow> {
  return request<DataEntryRow>(`/data-entries/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(update),
  })
}

/** DELETE /data-entries/{id} — remove an entry */
export async function deleteDataEntry(id: number): Promise<void> {
  const res = await fetch(`${BASE_URL}/data-entries/${id}`, { method: 'DELETE' })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const detail = (body as { detail?: string }).detail ?? res.statusText
    throw new Error(`${res.status}: ${detail}`)
  }
}

/** GET /chat-history — fetch up to 100 most recent chat messages ordered ascending */
export async function getChatHistory(): Promise<ChatMessageRow[]> {
  return request<ChatMessageRow[]>('/chat-history')
}

/** POST /chat-history — persist a new chat message */
export async function createChatMessage(msg: ChatMessageCreate): Promise<ChatMessageRow> {
  return request<ChatMessageRow>('/chat-history', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(msg),
  })
}

/** DELETE /chat-history — wipe all chat messages from the database */
export async function clearChatHistory(): Promise<void> {
  const res = await fetch(`${BASE_URL}/chat-history`, { method: 'DELETE' })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const detail = (body as { detail?: string }).detail ?? res.statusText
    throw new Error(`${res.status}: ${detail}`)
  }
}

/** GET /meralco-rate — fetch current Meralco residential rate (cached 24h) */
export async function getMeralcoRate(): Promise<MeralcoRateResponse> {
  return request<MeralcoRateResponse>('/meralco-rate')
}

/** POST /meralco-rate/refresh — force a fresh scrape, bypassing the 24h cache */
export async function refreshMeralcoRate(): Promise<MeralcoRateResponse> {
  return request<MeralcoRateResponse>('/meralco-rate/refresh', { method: 'POST' })
}
