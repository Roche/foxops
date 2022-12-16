import { Theme } from '@emotion/react'
import styled from '@emotion/styled'
import { forwardRef } from 'react'
import { transparentize } from '../../../styling/colors'

type Size = 'small' | 'large'
type Variant = 'primary' | 'danger'
interface ButtonBoxProps {
  size?: Size,
  variant?: Variant
}

const getBgByState = ({ theme, variant, disabled }: { theme: Theme, disabled?: boolean, variant?: Variant }) => {
  if (disabled) {
    return theme.colors.darkGrey
  }
  if (variant === 'danger') {
    return theme.colors.error
  }
  return theme.colors.orange
}

const ButtonBox = styled('button')<ButtonBoxProps>(({ theme, size, disabled, variant }) => {
  const backgroundColor = getBgByState({ theme, variant, disabled })
  return {
    textDecoration: 'none',
    color: '#fff',
    border: 'none',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: size === 'small' ? '32px' : '38px',
    fontSize: size === 'small' ? '12px' : '16px',
    borderRadius: 4,
    background: backgroundColor,
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
      boxShadow: `0 0 0 2px ${variant === 'danger' ? transparentize(theme.colors.error, .5) : theme.colors.paleOrange}`
    },
    ':disabled': {
      background: theme.colors.darkGrey,
      opacity: 0.7,
      cursor: 'not-allowed'
    }
  }
})

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
  border: 2px solid ${p => transparentize(p.theme.colors.contrastText, 0.4)};
  border-bottom-color: ${p => p.theme.colors.contrastText};
  border-radius: 50%;
  display: inline-block;
  box-sizing: border-box;
  animation: rotation 1s linear infinite;
`

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode,
  variant?: Variant,
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
  <ButtonLinkBox data-testid={dataTestid} ref={ref} type="button" {...props}>
    <ButtonInnerBox>{children}</ButtonInnerBox>
  </ButtonLinkBox>
))

ButtonLink.displayName = 'ButtonLink'
