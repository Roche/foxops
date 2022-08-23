import styled from '@emotion/styled'

interface IconButtonProps {
  active?: boolean
}

export const IconButton = styled('button')<IconButtonProps>(({ theme, active }) => ({
  background: 'none',
  border: `1px solid ${active ? 'transparent' : theme.colors.iconButtonBorder}`,
  padding: 6,
  borderRadius: '8px',
  color: active ? theme.colors.textContrast : theme.colors.iconButtonColor,
  position: 'relative',
  overflow: 'hidden',
  cursor: 'pointer',
  width: 38,
  minWidth: 38,
  maxWidth: 38,
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
  '&:hover::after': {
    transitionTimingFunction: 'var(--ease-in)',
    opacity: active ? 0.1 : 0.3
  },
  '&:hover': {
    transitionTimingFunction: 'var(--ease-in)'
  },
  '&:active::after': {
    opacity: 0.6
  }
}))
