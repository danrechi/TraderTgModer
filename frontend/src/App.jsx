import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Sources from './pages/Sources'
import News from './pages/News'
import Rules from './pages/Rules'
import Login from './pages/Login'

//приватный маршрут — редирект на /login если не авторизован
function PrivateRoute({ children }) {
  const { isAuth } = useAuth()
  return isAuth ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Страница входа — публичная */}
        <Route path="/login" element={<Login />} />

        {/* Все остальные маршруты — только для авторизованных */}
        <Route
          path="/"
          element={<PrivateRoute><Layout /></PrivateRoute>}
        >
          <Route index element={<Dashboard />} />
          <Route path="sources" element={<Sources />} />
          <Route path="news"    element={<News />} />
          <Route path="rules"   element={<Rules />} />
          <Route path="*"       element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
