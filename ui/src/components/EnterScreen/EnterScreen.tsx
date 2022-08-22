import { useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { api } from '../../services/api'
import { useAuthStore } from '../../stores/auth'
import { Layout } from '../Layout/Layout'

export const EnterScreen = () => {
  const { token } = useAuthStore()
  if (token) api.setToken(token)
  useEffect(() => {
    api.setToken(token)
  }, [token])
  if (!token) {
    return <Navigate to="/login" />
  }
  return <Layout />
}
