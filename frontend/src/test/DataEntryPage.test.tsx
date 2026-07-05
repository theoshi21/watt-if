import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { DataEntryPage } from '../pages/DataEntryPage'
import * as client from '../api/client'

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock('../api/client', () => ({
  getDataEntries: vi.fn(),
  createDataEntry: vi.fn(),
}))

// Mock UploadPanel so we can trigger onUploadSuccess without real API calls
vi.mock('../components/UploadPanel', () => ({
  UploadPanel: ({ onUploadSuccess }: { onUploadSuccess?: (f: string) => void }) => (
    <button onClick={() => onUploadSuccess?.('test.csv')}>Trigger Upload Success</button>
  ),
}))

const mockGetDataEntries = client.getDataEntries as ReturnType<typeof vi.fn>
const mockCreateDataEntry = client.createDataEntry as ReturnType<typeof vi.fn>

describe('DataEntryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Default: GET returns empty list
    mockGetDataEntries.mockResolvedValue([])
  })

  // ── Initial state ─────────────────────────────────────────────────────────

  it('shows empty-state message when no entries have been recorded', async () => {
    render(<DataEntryPage />)
    // Wait for the initial fetch to settle
    await waitFor(() => {
      expect(screen.getByText('No entries recorded yet.')).toBeInTheDocument()
    })
  })

  it('calls getDataEntries on mount', async () => {
    render(<DataEntryPage />)
    await waitFor(() => {
      expect(mockGetDataEntries).toHaveBeenCalledTimes(1)
    })
  })

  // ── Form structure ────────────────────────────────────────────────────────

  it('renders Month, kWh, Bill Amount and Label fields', async () => {
    render(<DataEntryPage />)
    await waitFor(() => expect(mockGetDataEntries).toHaveBeenCalled())
    expect(screen.getByLabelText(/month/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/kwh/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/bill amount/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/label/i)).toBeInTheDocument()
  })

  // ── Validation ────────────────────────────────────────────────────────────

  it('does NOT submit when Month is empty', async () => {
    render(<DataEntryPage />)
    await waitFor(() => expect(mockGetDataEntries).toHaveBeenCalled())

    // Fill kWh but leave month blank
    fireEvent.change(screen.getByLabelText(/kwh/i), { target: { value: '120' } })
    fireEvent.click(screen.getByRole('button', { name: /submit/i }))

    // createDataEntry should NOT have been called
    expect(mockCreateDataEntry).not.toHaveBeenCalled()
    // empty state still shown
    expect(screen.getByText('No entries recorded yet.')).toBeInTheDocument()
  })

  it('shows kWh validation error when kWh is invalid', async () => {
    render(<DataEntryPage />)
    await waitFor(() => expect(mockGetDataEntries).toHaveBeenCalled())

    // Fill month but leave kWh blank
    fireEvent.change(screen.getByLabelText(/month/i), { target: { value: '2024-06' } })
    fireEvent.click(screen.getByRole('button', { name: /submit/i }))

    expect(screen.getByText(/kwh must be/i)).toBeInTheDocument()
    expect(mockCreateDataEntry).not.toHaveBeenCalled()
  })

  // ── Valid submission ──────────────────────────────────────────────────────

  it('appends a Manual row to the history log on valid submit', async () => {
    const newRow = {
      id: 1,
      year_month: '2024-06',
      kwh: 250,
      bill_amount: null,
      label: 'June bill',
      source: 'Manual',
      created_at: '2024-06-15T14:30:00Z',
    }
    mockCreateDataEntry.mockResolvedValue(newRow)

    render(<DataEntryPage />)
    await waitFor(() => expect(mockGetDataEntries).toHaveBeenCalled())

    fireEvent.change(screen.getByLabelText(/month/i), { target: { value: '2024-06' } })
    fireEvent.change(screen.getByLabelText(/kwh/i), { target: { value: '250' } })
    fireEvent.change(screen.getByLabelText(/label/i), { target: { value: 'June bill' } })

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /submit/i }))
    })

    await waitFor(() => {
      expect(screen.getByText('2024-06')).toBeInTheDocument()
      expect(screen.getByText('250')).toBeInTheDocument()
      expect(screen.getByText('June bill')).toBeInTheDocument()
      expect(screen.getByText('Manual')).toBeInTheDocument()
    })
  })

  it('clears form fields after a valid submit', async () => {
    const newRow = {
      id: 1,
      year_month: '2024-06',
      kwh: 250,
      bill_amount: null,
      label: null,
      source: 'Manual',
      created_at: '2024-06-15T14:30:00Z',
    }
    mockCreateDataEntry.mockResolvedValue(newRow)

    render(<DataEntryPage />)
    await waitFor(() => expect(mockGetDataEntries).toHaveBeenCalled())

    const monthInput = screen.getByLabelText(/month/i) as HTMLInputElement
    const kwhInput = screen.getByLabelText(/kwh/i) as HTMLInputElement

    fireEvent.change(monthInput, { target: { value: '2024-06' } })
    fireEvent.change(kwhInput, { target: { value: '250' } })

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /submit/i }))
    })

    await waitFor(() => {
      expect(monthInput.value).toBe('')
      expect(kwhInput.value).toBe('')
    })
  })

  // ── CSV Upload ────────────────────────────────────────────────────────────

  it('calls createDataEntry with CSV Upload source when onUploadSuccess fires', async () => {
    const csvRow = {
      id: 2,
      year_month: expect.any(String),
      kwh: 0,
      bill_amount: null,
      label: 'test.csv',
      source: 'CSV Upload',
      created_at: '2024-06-15T14:30:00Z',
    }
    mockCreateDataEntry.mockResolvedValue({
      id: 2,
      year_month: '2024-06',
      kwh: 0,
      bill_amount: null,
      label: 'test.csv',
      source: 'CSV Upload',
      created_at: '2024-06-15T14:30:00Z',
    })

    render(<DataEntryPage />)
    await waitFor(() => expect(mockGetDataEntries).toHaveBeenCalled())

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /trigger upload success/i }))
    })

    await waitFor(() => {
      expect(mockCreateDataEntry).toHaveBeenCalledWith(
        expect.objectContaining({ source: 'CSV Upload', label: 'test.csv' }),
      )
    })
  })

  it('displays the CSV Upload row in the history table after upload', async () => {
    mockCreateDataEntry.mockResolvedValue({
      id: 2,
      year_month: '2024-06',
      kwh: 0,
      bill_amount: null,
      label: 'test.csv',
      source: 'CSV Upload',
      created_at: '2024-06-15T14:30:00Z',
    })

    render(<DataEntryPage />)
    await waitFor(() => expect(mockGetDataEntries).toHaveBeenCalled())

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /trigger upload success/i }))
    })

    await waitFor(() => {
      expect(screen.getByText('CSV Upload')).toBeInTheDocument()
      expect(screen.getByText('test.csv')).toBeInTheDocument()
    })
  })

  // ── Table column headers ───────────────────────────────────────────────────

  it('renders history table with correct column headers when rows exist', async () => {
    mockGetDataEntries.mockResolvedValue([
      {
        id: 1,
        year_month: '2024-01',
        kwh: 100,
        bill_amount: 500,
        label: 'Jan',
        source: 'Manual',
        created_at: '2024-01-15T00:00:00Z',
      },
    ])

    render(<DataEntryPage />)
    await waitFor(() => {
      // Use getAllByText since 'Month' appears in both the form label and table header
      expect(screen.getAllByText(/^month$/i).length).toBeGreaterThanOrEqual(1)
      // These column headers are unique in the table
      expect(screen.getByText('Bill Amount')).toBeInTheDocument()
      expect(screen.getByText('Source')).toBeInTheDocument()
      expect(screen.getByText('Submitted At')).toBeInTheDocument()
    })
  })

  // ── Error handling ────────────────────────────────────────────────────────

  it('shows fetch error inline when GET /data-entries fails', async () => {
    mockGetDataEntries.mockRejectedValue(new Error('Network error'))

    render(<DataEntryPage />)
    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument()
    })
  })

  it('shows submit error inline when POST /data-entries fails', async () => {
    mockCreateDataEntry.mockRejectedValue(new Error('Server error'))

    render(<DataEntryPage />)
    await waitFor(() => expect(mockGetDataEntries).toHaveBeenCalled())

    fireEvent.change(screen.getByLabelText(/month/i), { target: { value: '2024-06' } })
    fireEvent.change(screen.getByLabelText(/kwh/i), { target: { value: '250' } })

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /submit/i }))
    })

    await waitFor(() => {
      expect(screen.getByText(/server error/i)).toBeInTheDocument()
    })
  })
})
