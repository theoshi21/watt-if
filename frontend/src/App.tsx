import { Routes, Route, Navigate } from 'react-router-dom'
import AppShell from './components/AppShell'
import DashboardPage from './pages/DashboardPage'
import ForecastPage from './pages/ForecastPage'
import AskPage from './pages/AskPage'
import DataEntryPage from './pages/DataEntryPage'
import PriceCalculatorPage from './pages/PriceCalculatorPage'

export function App() {
  return (
    <Routes>
      <Route path="/" element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="forecast" element={<ForecastPage />} />
        <Route path="ask" element={<AskPage />} />
        <Route path="data-entry" element={<DataEntryPage />} />
        <Route path="calculator" element={<PriceCalculatorPage />} />
        <Route path="*" element={<Navigate replace to="/" />} />
      </Route>
    </Routes>
  )
}

export default App
