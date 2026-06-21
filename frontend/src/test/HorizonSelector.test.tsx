import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { HorizonSelector } from '../components/HorizonSelector'

describe('HorizonSelector', () => {
  it('renders all three horizon buttons', () => {
    render(<HorizonSelector selected={3} onChange={vi.fn()} />)
    expect(screen.getByText('1m')).toBeInTheDocument()
    expect(screen.getByText('3m')).toBeInTheDocument()
    expect(screen.getByText('6m')).toBeInTheDocument()
  })

  it('marks the selected button as pressed', () => {
    render(<HorizonSelector selected={3} onChange={vi.fn()} />)
    expect(screen.getByText('3m')).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByText('1m')).toHaveAttribute('aria-pressed', 'false')
  })

  it('calls onChange with the clicked horizon', () => {
    const onChange = vi.fn()
    render(<HorizonSelector selected={3} onChange={onChange} />)
    fireEvent.click(screen.getByText('6m'))
    expect(onChange).toHaveBeenCalledWith(6)
  })

  it('disables all buttons when disabled=true', () => {
    render(<HorizonSelector selected={1} onChange={vi.fn()} disabled />)
    screen.getAllByRole('button').forEach((btn) => {
      expect(btn).toBeDisabled()
    })
  })
})
