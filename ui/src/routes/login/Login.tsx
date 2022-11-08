import styled from '@emotion/styled'
// import Alert from '@mui/material/Alert' - would be nice but not working for now... :-(
import { Navigate, useSearchParams } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import { useAuthStore } from '../../stores/auth'
import { Button } from '../../components/common/Button/Button'
import { Hug } from '../../components/common/Hug/Hug'
import { Logo } from '../../components/common/Logo/Logo'
import { api } from '../../services/api'
import { auth } from '../../services/auth'

const Wrapper = styled.div({
  height: '100vh',
  display: 'flex'
})

const FormComponent = styled.form({
  maxWidth: '300px',
  flexGrow: 1,
  margin: 'auto',
  height: 300,
  textAlign: 'center',
  padding: 8,
  'textarea.TextField': {
    fontFamily: 'var(--monospace-font)',
    maxHeight: 200,
    minHeight: 50
  }
})

export const Login = () => {
  const loginRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { token, setToken } = useAuthStore()
  const [searchParams, setSearchParam] = useSearchParams()
  const code = searchParams.get('code')
  const state = searchParams.get('state')
  const login_url = `/auth/login?redirect_uri=${window.location.href.split('?')[0]}` // remove parameters if any

  useEffect(() => {
    if (code && state) getToken()
  }, [])

  if (token) return (<Navigate to="/incarnations" />)

  const getToken = async () => {
    if (code && state) {
      setLoading(true)
      try {
        const token = await auth.fetchToken(code, state)
        api.setToken(token)
        setToken(token)
      } catch (error) {
        console.log('error', error)
        setError('Invalid token')
        loginRef.current?.focus()
        api.setToken(null)
      } finally {
        setLoading(false)
      }
    }
  }

  const onFormSubmit: React.FormEventHandler = e => {
    e.preventDefault()
    window.location.replace(login_url)
  }

  return (
    <Wrapper data-testid="Login-Wrapper">
      <FormComponent onSubmit={onFormSubmit} data-testid="Login-Form">
        <Hug mb={40}>
          <Logo size={62} />
        </Hug>
        <Button loading={loading} type="submit" data-testid="Login-Button" style={{ borderRadius: 20, width: '100%' }}>
          Login
        </Button>
      </FormComponent>
    </Wrapper>
  )
}
