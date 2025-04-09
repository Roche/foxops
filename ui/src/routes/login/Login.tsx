import styled from '@emotion/styled'
import { Navigate } from 'react-router-dom'
import { useState } from 'react'
import { useAuthStore } from '../../stores/auth'
import { Button } from '../../components/common/Button/Button'
import { Hug } from '../../components/common/Hug/Hug'
import { Logo } from '../../components/common/Logo/Logo'
import { TextField } from '../../components/common/TextField/TextField'
import { api } from '../../services/api'
import { auth } from '../../services/auth'
import { useForm } from 'react-hook-form'
import { AuthorizationToken } from 'interfaces/authz.types'

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

const Error = styled.span({
  color: 'red',
  fontSize: 12,
  marginTop: 4,
  display: 'block',
  minHeight: 14
})

const ProceedLink = styled.span({
  textDecoration: 'underline',
  cursor: 'pointer',
  ':hover': {
    textDecoration: 'none'
  }
})

const STAGES = {
  FIRST_INTERACTION: 'FIRST_INTERACTION',
  TOKEN_INPUT_SHOWN: 'TOKEN_INPUT_SHOWN'
}

export const Login = () => {
  const {
    register,
    getValues,
    setError,
    setFocus,
    handleSubmit,
    formState: { errors }
  } = useForm({
    defaultValues: {
      token: process.env.FOXOPS_STATIC_TOKEN || '',
      user: process.env.FOXOPS_STATIC_USERNAME || '',
      groups: process.env.FOXOPS_STATIC_GROUPS
    }

  })

  const [loading, setLoading] = useState(false)
  const [stage, setStage] = useState(STAGES.FIRST_INTERACTION)
  const { token, setToken, setUser } = useAuthStore()

  if (token) return (<Navigate to="/incarnations" />)
  const onProceedLinkClick = () => setStage(STAGES.TOKEN_INPUT_SHOWN)
  const checkToken = async () => {
    const TOKEN = getValues() as AuthorizationToken
    const groups = getValues('groups')

    if (groups && !/^ *[a-zA-Z_:\-0-9]+ *(, *[a-zA-Z_:\-0-9]+ *)*$/.test(groups)) {
      setError('groups', {
        type: 'manual',
        message: 'Invalid groups format'
      })
      setFocus('groups')
      return
    }

    api.setToken(TOKEN)
    setLoading(true)
    try {
      const user = await auth.checkToken()
      setUser(user)
      setToken(TOKEN)
    } catch (error) {
      console.log('error', error)
      setError('token', {
        type: 'manual',
        message: 'Invalid token'
      })
      setFocus('token')
      api.setToken(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Wrapper data-testid="Login-Wrapper">
      <FormComponent onSubmit={handleSubmit(checkToken)} data-testid="Login-Form">
        <Hug mb={40}>
          <Logo size={62} />
        </Hug>
        {stage === STAGES.FIRST_INTERACTION && <ProceedLink onClick={onProceedLinkClick}>Click to proceed</ProceedLink> }
        {stage === STAGES.TOKEN_INPUT_SHOWN && (
          <>
            <Hug mb={8} style={{ textAlign: 'left' }}>
              <TextField {...register('token', { required: true })} type="text" autoFocus placeholder="Enter your token" data-testid="Login-TextField" />
              <Error>{errors.token && errors.token.message || errors.token?.type}</Error>
            </Hug>
            <Hug mb={8} style={{ textAlign: 'left' }}>
              <TextField {...register('user', { required: true })} type="text" placeholder="Enter your username" data-testid="Login-Username" />
              <Error>{errors.user && errors.user.message || errors.user?.type}</Error>
            </Hug>
            <Hug mb={8} style={{ textAlign: 'left' }}>
              <TextField {...register('groups')} type="text" placeholder="Enter your groups (comma separated)" />
              <Error>{errors.groups && errors.groups.message || errors.groups?.type}</Error>
            </Hug>
            <Button loading={loading} type="submit" data-testid="Login-Button" style={{ borderRadius: 20, width: '100%' }}>
              Submit
            </Button>
          </>
        )}
      </FormComponent>
    </Wrapper>
  )
}
