import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ChatPanel } from '../components/ChatPanel'

// Mock the API client
vi.mock('../api/client', () => ({
  askQuestion: vi.fn(),
}))

import { askQuestion } from '../api/client'
const mockAsk = askQuestion as ReturnType<typeof vi.fn>

describe('ChatPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the question input and submit button', () => {
    render(<ChatPanel />)
    expect(screen.getByLabelText(/question input/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/submit question/i)).toBeInTheDocument()
  })

  it('submit button is disabled when input is empty', () => {
    render(<ChatPanel />)
    expect(screen.getByLabelText(/submit question/i)).toBeDisabled()
  })

  it('submit button is enabled when input has text', () => {
    render(<ChatPanel />)
    fireEvent.change(screen.getByLabelText(/question input/i), {
      target: { value: 'What is my forecast?' },
    })
    expect(screen.getByLabelText(/submit question/i)).not.toBeDisabled()
  })

  it('appends user message and assistant reply in chronological order', async () => {
    mockAsk.mockResolvedValue({ answer: 'Your forecast is 300 kWh.', sources: [] })
    render(<ChatPanel />)

    fireEvent.change(screen.getByLabelText(/question input/i), {
      target: { value: 'What is my forecast?' },
    })
    fireEvent.click(screen.getByLabelText(/submit question/i))

    // User message appears first
    await waitFor(() => {
      expect(screen.getByText('What is my forecast?')).toBeInTheDocument()
    })
    // Then assistant reply
    await waitFor(() => {
      expect(screen.getByText('Your forecast is 300 kWh.')).toBeInTheDocument()
    })

    // Check chronological order: user msg DOM position before assistant msg
    const articles = screen.getAllByRole('article')
    const userIdx = articles.findIndex((a) => a.textContent === 'What is my forecast?')
    const assistantIdx = articles.findIndex((a) => a.textContent === 'Your forecast is 300 kWh.')
    expect(userIdx).toBeLessThan(assistantIdx)
  })

  it('shows error message in thread when API call fails', async () => {
    mockAsk.mockRejectedValue(new Error('503: LLM unavailable'))
    render(<ChatPanel />)

    fireEvent.change(screen.getByLabelText(/question input/i), {
      target: { value: 'What is my forecast?' },
    })
    fireEvent.click(screen.getByLabelText(/submit question/i))

    await waitFor(() => {
      expect(screen.getByText(/could not display answer/i)).toBeInTheDocument()
    })
  })

  it('clears input after submission', async () => {
    mockAsk.mockResolvedValue({ answer: 'ok', sources: [] })
    render(<ChatPanel />)

    const input = screen.getByLabelText(/question input/i)
    fireEvent.change(input, { target: { value: 'Hello?' } })
    fireEvent.click(screen.getByLabelText(/submit question/i))

    await waitFor(() => {
      expect((input as HTMLInputElement).value).toBe('')
    })
  })

  it('enforces 500 char max on the input field', () => {
    render(<ChatPanel />)
    const input = screen.getByLabelText(/question input/i)
    expect(input).toHaveAttribute('maxLength', '500')
  })
})
