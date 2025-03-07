import { useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { api } from '../../services/api'
import { useAuthStore } from '../../stores/auth'
import { Layout, PageConfig } from '../Layout/Layout'

type EnterScreenProps = {
  config: PageConfig[]
}

export const EnterScreen = ({ config }: EnterScreenProps) => {
  const { token } = useAuthStore()
  if (token) api.setToken(token)
  useEffect(() => {
    api.setToken(token)
  }, [token])
  if (!token) {
    return <Navigate to="/login" />
  }
  return <Layout config={config} />
}
