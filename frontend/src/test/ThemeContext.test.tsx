import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import { ThemeProvider, useTheme } from '../context/ThemeContext'

// Simple consumer component
const ThemeConsumer: React.FC = () => {
  const { theme, toggleTheme } = useTheme()
  return (
    <div>
      <span data-testid="theme-value">{theme}</span>
      <button onClick={toggleTheme}>Toggle</button>
    </div>
  )
}

const STORAGE_KEY = 'wattif-theme'

beforeEach(() => {
  localStorage.clear()
  delete document.documentElement.dataset.theme
})

describe('ThemeProvider', () => {
  it('defaults to light theme when localStorage is empty', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    )
    expect(screen.getByTestId('theme-value').textContent).toBe('light')
  })

  it('initialises to dark theme when localStorage has "dark"', () => {
    localStorage.setItem(STORAGE_KEY, 'dark')
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    )
    expect(screen.getByTestId('theme-value').textContent).toBe('dark')
  })

  it('defaults to light when localStorage contains an unrecognised value', () => {
    localStorage.setItem(STORAGE_KEY, 'blue')
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    )
    expect(screen.getByTestId('theme-value').textContent).toBe('light')
  })

  it('sets document.documentElement.dataset.theme synchronously on initial render', () => {
    localStorage.setItem(STORAGE_KEY, 'dark')
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    )
    expect(document.documentElement.dataset.theme).toBe('dark')
  })

  it('toggles from light to dark', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    )
    fireEvent.click(screen.getByRole('button', { name: /toggle/i }))
    expect(screen.getByTestId('theme-value').textContent).toBe('dark')
  })

  it('toggles from dark back to light', () => {
    localStorage.setItem(STORAGE_KEY, 'dark')
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    )
    fireEvent.click(screen.getByRole('button', { name: /toggle/i }))
    expect(screen.getByTestId('theme-value').textContent).toBe('light')
  })

  it('persists the new theme to localStorage on toggle', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    )
    fireEvent.click(screen.getByRole('button', { name: /toggle/i }))
    expect(localStorage.getItem(STORAGE_KEY)).toBe('dark')
  })

  it('updates document.documentElement.dataset.theme on toggle', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    )
    fireEvent.click(screen.getByRole('button', { name: /toggle/i }))
    expect(document.documentElement.dataset.theme).toBe('dark')
  })
})

describe('useTheme', () => {
  it('throws when used outside ThemeProvider', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<ThemeConsumer />)).toThrow(
      'useTheme must be used within a ThemeProvider',
    )
    spy.mockRestore()
  })
})
