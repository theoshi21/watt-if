import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { ForecastProvider } from './context/ForecastContext'
import './styles/tokens.css'
import './styles/index.css'
import { App } from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <ForecastProvider>
          <App />
        </ForecastProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>
)
