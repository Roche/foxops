import { Theme } from '@emotion/react'
import styled from '@emotion/styled'
import { Plus } from '../Icons/Plus'

const Box = styled.button(({ theme }: { theme: Theme }) => ({
  border: 'none',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  position: 'fixed',
  zIndex: theme.zIndex.floatingActionButton,
  bottom: 40,
  right: 40,
  width: 56,
  height: 56,
  borderRadius: '50%',
  backgroundColor: theme.colors.orange,
  color: theme.colors.contrastText,
  cursor: 'pointer',
  boxShadow: theme.effects.actionButtonShadow,
  transition: 'box-shadow .25s var(--ease-out)',
  overflow: 'hidden',
  '::after': {
    content: '""',
    position: 'absolute',
    zIndex: 2,
    width: '100%',
    height: '100%',
    top: 0,
    left: 0,
    transition: 'opacity .2s var(--ease-out)',
    backgroundColor: theme.colors.grey,
    opacity: 0
  },
  ':hover::after': {
    transitionTimingFunction: 'var(--ease-in)',
    opacity: 0.1
  },
  ':active': {
    transitionTimingFunction: 'var(--ease-in)',
    boxShadow: theme.effects.actionButtonHoverShadow
  },
  ':focus': {
    outline: 'none'
  }
}))

export const FloatingActionButton = ({ ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
  <Box type="button" {...props}>
    <Plus />
  </Box>
)
