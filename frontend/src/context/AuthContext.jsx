import { createContext, useContext, useState } from 'react'

//контекст авторизации — хранит токен и имя пользователя
const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [user,  setUser]  = useState(localStorage.getItem('user'))

  //login: сохраняем токен и имя в localStorage и в state
  function login(accessToken, username) {
    localStorage.setItem('token', accessToken)
    localStorage.setItem('user', username)
    setToken(accessToken)
    setUser(username)
  }

  //logout: очищаем всё
  function logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isAuth: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

//хук для удобного доступа к контексту в любом компоненте
export function useAuth() {
  return useContext(AuthContext)
}
