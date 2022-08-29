import styled from '@emotion/styled'
import { Navigate } from 'react-router-dom'
import { useState } from 'react'
import { useAuthStore } from '../../stores/auth'
import { Button } from '../../components/common/Button/Button'
import { Hug } from '../../components/common/Hug/Hug'
import { Logo } from '../../components/common/Logo/Logo'
import { TextField } from '../../components/common/TextField/TextField'

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
  const [_token, _setToken] = useState(process.env.FOXOPS_STATIC_TOKEN as string)
  const [stage, setStage] = useState(STAGES.FIRST_INTERACTION)
  const { token, setToken } = useAuthStore()
  if (token) return (<Navigate to="/incarnations" />)
  const onChangeToken: React.ChangeEventHandler<HTMLInputElement> = e => {
    _setToken(e.target.value)
  }
  const onProceedLinkClick = () => setStage(STAGES.TOKEN_INPUT_SHOWN)
  const onFormSubmit: React.FormEventHandler = e => {
    e.preventDefault()
    if (_token) {
      setToken(_token)
    }
  }
  return (
    <Wrapper data-testid="Login-Wrapper">
      <FormComponent onSubmit={onFormSubmit} data-testid="Login-Form">
        <Hug mb={40}>
          <Logo size={62} />
        </Hug>
        {stage === STAGES.FIRST_INTERACTION && <ProceedLink onClick={onProceedLinkClick}>Click to proceed</ProceedLink> }
        {stage === STAGES.TOKEN_INPUT_SHOWN && (
          <>
            <Hug mb={16}>
              <TextField type="text" autoFocus value={_token} placeholder="Enter your token" onChange={onChangeToken} data-testid="Login-TextField" />
            </Hug>
            <Button type="submit" data-testid="Login-Button" style={{ borderRadius: 20, width: '100%' }}>
              Submit
            </Button>
          </>
        )}
      </FormComponent>
    </Wrapper>
  )
}
