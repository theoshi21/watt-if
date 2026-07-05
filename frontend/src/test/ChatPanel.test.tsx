import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ChatPanel } from '../components/ChatPanel'

// Mock the API client — must include all functions used by ChatPanel
vi.mock('../api/client', () => ({
  streamQuestion: vi.fn(),
  getChatHistory: vi.fn(),
  createChatMessage: vi.fn(),
}))

import { streamQuestion, getChatHistory, createChatMessage } from '../api/client'
const mockStream = vi.mocked(streamQuestion)
const mockGetHistory = vi.mocked(getChatHistory)
const mockCreateMessage = vi.mocked(createChatMessage)

describe('ChatPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Default: history loads with empty array, createChatMessage succeeds
    mockGetHistory.mockResolvedValue([])
    mockCreateMessage.mockResolvedValue({ id: 1, role: 'user', text: '', created_at: '' })
  })

  it('renders the question input and submit button', async () => {
    await act(async () => { render(<ChatPanel />) })
    expect(screen.getByLabelText(/question input/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/submit question/i)).toBeInTheDocument()
  })

  it('submit button is disabled when input is empty', async () => {
    await act(async () => { render(<ChatPanel />) })
    // Wait for history loading to finish
    await waitFor(() => expect(screen.queryByLabelText(/loading chat history/i)).not.toBeInTheDocument())
    expect(screen.getByLabelText(/submit question/i)).toBeDisabled()
  })

  it('submit button is enabled when input has text', async () => {
    await act(async () => { render(<ChatPanel />) })
    // Wait for history loading to finish so historyLoading = false
    await waitFor(() => expect(screen.queryByLabelText(/loading chat history/i)).not.toBeInTheDocument())
    fireEvent.change(screen.getByLabelText(/question input/i), {
      target: { value: 'What is my forecast?' },
    })
    expect(screen.getByLabelText(/submit question/i)).not.toBeDisabled()
  })

  it('appends user message and assistant reply in chronological order', async () => {
    // Simulate streamQuestion calling onToken then onDone
    mockStream.mockImplementation(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      async (_q: string, onToken: (d: string) => void, onDone: (s: any[]) => void) => {
        onToken('Your forecast is 300 kWh.')
        onDone([])
      }
    )
    await act(async () => { render(<ChatPanel />) })
    // Wait for history to load
    await waitFor(() => expect(screen.queryByLabelText(/loading chat history/i)).not.toBeInTheDocument())

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
    const assistantIdx = articles.findIndex((a) =>
      a.textContent?.includes('Your forecast is 300 kWh.')
    )
    expect(userIdx).toBeLessThan(assistantIdx)
  })

  it('shows error message in thread when API call fails', async () => {
    mockStream.mockRejectedValue(new Error('503: LLM unavailable'))
    await act(async () => { render(<ChatPanel />) })
    await waitFor(() => expect(screen.queryByLabelText(/loading chat history/i)).not.toBeInTheDocument())

    fireEvent.change(screen.getByLabelText(/question input/i), {
      target: { value: 'What is my forecast?' },
    })
    fireEvent.click(screen.getByLabelText(/submit question/i))

    await waitFor(() => {
      expect(screen.getByText(/could not display answer/i)).toBeInTheDocument()
    })
  })

  it('clears input after submission', async () => {
    mockStream.mockImplementation(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      async (_q: string, _onToken: unknown, onDone: (s: any[]) => void) => {
        onDone([])
      }
    )
    await act(async () => { render(<ChatPanel />) })
    await waitFor(() => expect(screen.queryByLabelText(/loading chat history/i)).not.toBeInTheDocument())

    const input = screen.getByLabelText(/question input/i)
    fireEvent.change(input, { target: { value: 'Hello?' } })
    fireEvent.click(screen.getByLabelText(/submit question/i))

    await waitFor(() => {
      expect((input as HTMLInputElement).value).toBe('')
    })
  })

  it('enforces 500 char max on the input field', async () => {
    await act(async () => { render(<ChatPanel />) })
    const input = screen.getByLabelText(/question input/i)
    expect(input).toHaveAttribute('maxLength', '500')
  })

  it('submit button uses btn-primary class', async () => {
    await act(async () => { render(<ChatPanel />) })
    const button = screen.getByLabelText(/submit question/i)
    expect(button).toHaveClass('btn-primary')
  })

  it('outer section has card class', async () => {
    await act(async () => { render(<ChatPanel />) })
    const section = screen.getByRole('region', { name: /chat/i })
    expect(section).toHaveClass('card')
  })
})
