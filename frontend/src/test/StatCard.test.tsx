import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import StatCard from '../components/StatCard'

describe('StatCard', () => {
  it('renders a <dl> element', () => {
    const { container } = render(<StatCard label="Usage" value={42} />)
    expect(container.querySelector('dl')).toBeInTheDocument()
  })

  it('renders a <dt> element with the label text', () => {
    const { container } = render(<StatCard label="Usage" value={42} />)
    const dt = container.querySelector('dt')
    expect(dt).toBeInTheDocument()
    expect(dt).toHaveTextContent('Usage')
  })

  it('renders a <dd> element with the value text', () => {
    const { container } = render(<StatCard label="Usage" value={42} />)
    const dd = container.querySelector('dd')
    expect(dd).toBeInTheDocument()
    expect(dd).toHaveTextContent('42')
  })

  it('appends the unit to the <dd> value when unit prop is provided', () => {
    const { container } = render(<StatCard label="Usage" value={42} unit="kWh" />)
    const dd = container.querySelector('dd')
    expect(dd).toHaveTextContent('42 kWh')
  })

  it('renders without unit when unit prop is omitted', () => {
    const { container } = render(<StatCard label="Usage" value={42} />)
    const dd = container.querySelector('dd')
    expect(dd?.textContent).toBe('42')
  })

  it('<dd> has fontFamily set to var(--font-mono)', () => {
    const { container } = render(<StatCard label="Usage" value={42} />)
    const dd = container.querySelector('dd') as HTMLElement
    expect(dd.style.fontFamily).toBe('var(--font-mono)')
  })

  it('<dt> has fontFamily set to var(--font-sans)', () => {
    const { container } = render(<StatCard label="Usage" value={42} />)
    const dt = container.querySelector('dt') as HTMLElement
    expect(dt.style.fontFamily).toBe('var(--font-sans)')
  })
})
