import { useEffect } from 'react'
import { api } from '../../services/api'
import { useAuthStore } from '../../stores/auth'
import { IncarnationsList } from '../Incarnations/List'
import { Login } from '../Login/Login'

export const EnterScreen = () => {
  const { token } = useAuthStore()
  if (token) api.setToken(token)
  useEffect(() => {
    api.setToken(token)
  }, [token])
  if (!token) {
    return <Login />
  }
  return <IncarnationsList />
}
