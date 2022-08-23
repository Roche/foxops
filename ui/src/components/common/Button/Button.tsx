import styled from '@emotion/styled'

interface ButtonBoxProps {
  size?: 'small'
}

const ButtonBox = styled('button')<ButtonBoxProps>(({ theme, size, disabled }) => ({
  textDecoration: 'none',
  color: '#fff',
  border: 'none',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  height: size === 'small' ? '30px' : '40px',
  fontSize: size === 'small' ? '12px' : '16px',
  borderRadius: 4,
  background: disabled ? theme.colors.darkGrey : theme.effects.orangeGradient,
  position: 'relative',
  overflow: 'hidden',
  paddingLeft: size === 'small' ? 8 : 16,
  paddingRight: size === 'small' ? 8 : 16,
  cursor: disabled ? 'not-allowed' : 'pointer',
  opacity: disabled ? 0.7 : 1,
  ':not(:disabled)::after': {
    content: disabled ? undefined : '""',
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
  },
  ':disabled': {
    background: theme.colors.darkGrey,
    opacity: 0.7,
    cursor: 'not-allowed'
  }
}))

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode,
  size?: 'small'
}

export const Button = ({ children, ...props }: ButtonProps) => (
  <ButtonBox {...props}>
    <span>{children}</span>
  </ButtonBox>
)

interface ButtonLinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  children: React.ReactNode,
  size?: 'small',
  disabled?: boolean
}

const ButtonLinkBox = ButtonBox.withComponent('a')

export const ButtonLink = ({ children, ...props }: ButtonLinkProps) => (
  <ButtonLinkBox {...props} {...props}>
    <span>{children}</span>
  </ButtonLinkBox>
)
