import styled from '@emotion/styled'
import { forwardRef } from 'react'
import { transparentize } from '../../../styling/colors'

type Size = 'small' | 'large'
interface ButtonBoxProps {
  size?: Size
}

const ButtonBox = styled('button')<ButtonBoxProps>(({ theme, size, disabled }) => ({
  textDecoration: 'none',
  color: '#fff',
  border: 'none',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  height: size === 'small' ? '30px' : '38px',
  fontSize: size === 'small' ? '12px' : '16px',
  borderRadius: 4,
  background: disabled ? theme.colors.darkGrey : theme.colors.orange,
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

const ButtonInnerBox = styled.span`
  position: relative;
  z-index: 2;
  display: inline-flex;
  align-content: center;
  justify-content: center;
`

const Loader = styled.span`
  width: 16px;
  height: 16px;
  border: 2px solid ${p => transparentize(p.theme.colors.textContrast, 0.4)};
  border-bottom-color: ${p => p.theme.colors.textContrast};
  border-radius: 50%;
  display: inline-block;
  box-sizing: border-box;
  animation: rotation 1s linear infinite;
`

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode,
  size?: Size,
  dataTestid?: string,
  loading?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(({ children, dataTestid, loading, ...props }, ref) => (
  <ButtonBox data-testid={dataTestid} ref={ref} {...props}>
    <ButtonInnerBox>{children}{loading && <Loader style={{ marginLeft: children ? 8 : 0 }} />}</ButtonInnerBox>
  </ButtonBox>
))

Button.displayName = 'Button'

interface ButtonLinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  children: React.ReactNode,
  size?: Size
  disabled?: boolean
  dataTestid?: string
}

const ButtonLinkBox = ButtonBox.withComponent('a')

export const ButtonLink = forwardRef<HTMLAnchorElement, ButtonLinkProps>(({ children, dataTestid, ...props }, ref) => (
  <ButtonLinkBox data-testid={dataTestid} ref={ref} {...props}>
    <ButtonInnerBox>{children}</ButtonInnerBox>
  </ButtonLinkBox>
))

ButtonLink.displayName = 'ButtonLink'
