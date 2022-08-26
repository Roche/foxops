import styled from '@emotion/styled'

interface IconButtonProps {
  active?: boolean,
  flying?: boolean
}

export const IconButton = styled('button')<IconButtonProps>(({ theme, active, flying }) => ({
  background: 'none',
  border: flying ? 'none' : `1px solid ${active ? 'transparent' : theme.colors.iconButtonBorder}`,
  padding: 6,
  borderRadius: '8px',
  color: active ? theme.colors.textContrast : theme.colors.iconButtonColor,
  position: 'relative',
  overflow: 'hidden',
  cursor: 'pointer',
  width: 38,
  minWidth: 38,
  maxWidth: 38,
  transition: 'box-shadow .2s var(--base-easing)',
  svg: {
    verticalAlign: 'middle',
    position: 'relative',
    zIndex: 3
  },
  '&::before': {
    content: '""',
    position: 'absolute',
    zIndex: 1,
    width: '100%',
    height: '100%',
    top: 0,
    left: 0,
    transition: 'transform .1s',
    transitionTimingFunction: active ? 'var(--ease-in)' : 'var(--ease-out)',
    backgroundImage: theme.effects.orangeGradient,
    transform: `scale(${Number(!!active)})`
  },
  '&::after': {
    content: '""',
    position: 'absolute',
    zIndex: 2,
    width: '100%',
    height: '100%',
    top: 0,
    left: 0,
    transition: 'opacity .2s var(--ease-out)',
    backgroundColor: theme.colors.iconButtonCurtain,
    opacity: 0
  },
  '&:hover:not(:disabled)::after': {
    transitionTimingFunction: 'var(--ease-in)',
    opacity: active ? 0.1 : 0.3
  },
  '&:hover:not(:disabled)': {
    transitionTimingFunction: 'var(--ease-in)'
  },
  '&:active::after': {
    opacity: 0.6
  },
  ':focus': {
    outline: 'none',
    boxShadow: `0 0 0 2px ${theme.colors.paleOrange}`
  },
  ':disabled': {
    borderStyle: 'dashed',
    opacity: .8,
    cursor: 'not-allowed'
  }
}))
