import styled from '@emotion/styled'

interface IconButtonProps {
  active?: boolean,
  flying?: boolean,
  size?: 'medium' | 'small'
}

export const IconButton = styled('button')<IconButtonProps>(({ theme, active, flying, size }) => {
  const _size = size === 'small' ? 24 : size === 'medium' ? 32 : 38
  const borderRadius = size ? 4 : 8
  const svgSize = size ? 16 : 24
  return ({
    background: 'none',
    border: flying ? 'none' : `1px solid ${active ? 'transparent' : theme.colors.iconButtonBorder}`,
    padding: size === 'small' ? 0 : 6,
    borderRadius,
    color: active ? theme.colors.contrastText : theme.colors.iconButtonColor,
    position: 'relative',
    overflow: 'hidden',
    cursor: 'pointer',
    width: _size,
    minWidth: _size,
    maxWidth: _size,
    height: _size,
    minHeight: _size,
    maxHeight: _size,
    transition: 'box-shadow .2s var(--base-easing)',
    svg: {
      verticalAlign: 'middle',
      position: 'relative',
      zIndex: 3,
      width: svgSize,
      height: svgSize
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
      backgroundColor: theme.colors.orange,
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
  })
})
