import styled from '@emotion/styled'
import { useState } from 'react'
import { api } from '../../services/api'
import { useAuthStore } from '../../stores/auth'
import { Logo } from '../common/Logo/Logo'
import { TextField } from '../common/TextField/TextField'

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

const Button = styled.button({
  color: '#fff',
  border: 'none',
  display: 'block',
  width: '100%',
  height: '40px',
  borderRadius: 20,
  background: 'linear-gradient(133deg, var(--orange), var(--pale-orange))',
  marginTop: 8,
  position: 'relative',
  overflow: 'hidden',
  '::after': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    zIndex: 1,
    background: '#000',
    opacity: 0,
    transition: 'opacity 0.1s var(--easing)'
  },
  ':hover::after': {
    opacity: 0.05
  },
  ':active::after': {
    opacity: 0.1
  },
  span: {
    position: 'relative',
    zIndex: 2
  },
  ':focus': {
    outline: 'none',
    boxShadow: '0 0 0 2px var(--pale-orange)'
  }
})

const STAGES = {
  FIRST_INTERACTION: 'FIRST_INTERACTION',
  TOKEN_INPUT_SHOWN: 'TOKEN_INPUT_SHOWN'
}

export const Login = () => {
  const [_token, _setToken] = useState('')
  const [stage, setStage] = useState(STAGES.FIRST_INTERACTION)
  const { setToken } = useAuthStore()
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
        <Logo />
        {stage === STAGES.FIRST_INTERACTION && <ProceedLink onClick={onProceedLinkClick}>Click to proceed</ProceedLink> }
        {stage === STAGES.TOKEN_INPUT_SHOWN && (
          <>
            <TextField rows={3} type="textarea" autoFocus value={_token} placeholder="Enter your token" onChange={onChangeToken} data-testid="Login-TextField" />
            <Button type="submit" data-testid="Login-Button">
              <span>Submit</span>
            </Button>
          </>
        )}
      </FormComponent>
    </Wrapper>
  )
}
