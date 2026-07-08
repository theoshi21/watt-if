import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import AuthGuard from './components/AuthGuard'
import AppShell from './components/AppShell'
import DashboardPage from './pages/DashboardPage'
import ForecastPage from './pages/ForecastPage'
import AskPage from './pages/AskPage'
import DataEntryPage from './pages/DataEntryPage'
import PriceCalculatorPage from './pages/PriceCalculatorPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import AccountSettingsPage from './pages/AccountSettingsPage'

export function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public routes (outside AuthGuard) */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected routes (inside AuthGuard) */}
        <Route element={<AuthGuard />}>
          <Route path="/" element={<AppShell />}>
            <Route index element={<DashboardPage />} />
            <Route path="forecast" element={<ForecastPage />} />
            <Route path="ask" element={<AskPage />} />
            <Route path="data-entry" element={<DataEntryPage />} />
            <Route path="calculator" element={<PriceCalculatorPage />} />
            <Route path="account" element={<AccountSettingsPage />} />
            <Route path="*" element={<Navigate replace to="/" />} />
          </Route>
        </Route>
      </Routes>
    </AuthProvider>
  )
}

export default App
