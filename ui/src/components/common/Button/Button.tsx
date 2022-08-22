import styled from '@emotion/styled'

export const ButtonBox = styled.button(({ theme }) => ({
  color: '#fff',
  border: 'none',
  display: 'block',
  height: '40px',
  borderRadius: 4,
  background: theme.effects.orangeGradient,
  position: 'relative',
  overflow: 'hidden',
  paddingLeft: 20,
  paddingRight: 20,
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
    transition: 'opacity 0.1s var(--base-easing)'
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
    boxShadow: `0 0 0 2px ${theme.colors.paleOrange}`
  }
}))

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode
}

export const Button = ({ children, ...props }: ButtonProps) => (
  <ButtonBox {...props}>
    <span>{children}</span>
  </ButtonBox>
)
