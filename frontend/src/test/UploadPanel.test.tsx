import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { UploadPanel } from '../components/UploadPanel'

vi.mock('../api/client', () => ({
  uploadCsv: vi.fn(),
  getTrainingStatus: vi.fn(),
}))

import { uploadCsv, getTrainingStatus } from '../api/client'
const mockUpload = uploadCsv as ReturnType<typeof vi.fn>
const mockStatus = getTrainingStatus as ReturnType<typeof vi.fn>

const csvFile = new File(['year_month,kwh,price\n2024-01,300,80\n'], 'bills.csv', {
  type: 'text/csv',
})

describe('UploadPanel', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders the file input label', () => {
    render(<UploadPanel />)
    expect(screen.getByText('Choose CSV')).toBeInTheDocument()
  })

  it('shows success notification on successful upload', async () => {
    mockUpload.mockResolvedValue({
      rows_received: 3,
      validation_status: 'ok',
      cleaning_report: null,
      retraining_triggered: false,
    })
    mockStatus.mockResolvedValue({ status: 'done' })

    render(<UploadPanel />)
    const input = screen.getByLabelText(/upload csv file/i)
    fireEvent.change(input, { target: { files: [csvFile] } })

    await waitFor(() => {
      expect(screen.getByRole('status')).toHaveTextContent(/model trained/i)
    }, { timeout: 5000 })
  })

  it('shows error notification on failed upload', async () => {
    mockUpload.mockRejectedValue(new Error('400: file too large'))
    render(<UploadPanel />)
    const input = screen.getByLabelText(/upload csv file/i)
    fireEvent.change(input, { target: { files: [csvFile] } })

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/400: file too large/i)
    })
  })

  it('calls onUploadSuccess callback when upload succeeds', async () => {
    const onSuccess = vi.fn()
    mockUpload.mockResolvedValue({
      rows_received: 1,
      validation_status: 'ok',
      cleaning_report: null,
      retraining_triggered: false,
    })
    mockStatus.mockResolvedValue({ status: 'done' })

    render(<UploadPanel onUploadSuccess={onSuccess} />)
    const input = screen.getByLabelText(/upload csv file/i)
    fireEvent.change(input, { target: { files: [csvFile] } })

    await waitFor(() => expect(onSuccess).toHaveBeenCalledOnce(), { timeout: 5000 })
  })
})
