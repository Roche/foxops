import styled from '@emotion/styled'
import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { transparentize } from '../../../styling/colors'
import { Hug } from '../../common/Hug/Hug'
import { DNA } from '../../common/Icons/DNA'

const Box = styled.div(({ theme }) => ({
  gridColumn: '1',
  gridRow: '2 / 3',
  position: 'relative',
  zIndex: theme.zIndex.aside
}))

interface ContainerProps {
  expanded: boolean
}
const Container = styled.div<ContainerProps>(({ theme, expanded }) => ({
  borderRight: `1px solid ${theme.colors.asideBorder}`,
  backgroundColor: theme.colors.asideBg,
  padding: 8,
  height: '100%',
  width: expanded ? 200 : 57,
  transition: 'width 0.1s',
  transitionTimingFunction: expanded ? 'var(--ease-in)' : 'var(--ease-out)',
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden'
}))

const AsideButton = styled(NavLink)(({ theme }) => ({
  textDecoration: 'none',
  whiteSpace: 'nowrap',
  border: 'none',
  padding: '0 4px',
  width: '100%',
  height: 40,
  borderRadius: 4,
  background: 'transparent',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  overflow: 'hidden',
  transition: 'background-color .2s var(--ease-out)',
  position: 'relative',
  color: theme.colors.text,
  '&.active': {
    color: theme.colors.textContrast,
    '&::after': {
      opacity: 1,
      transitionTimingFunction: 'var(--ease-in)'
    }
  },
  ':hover': {
    // borderColor: theme.colors.iconButtonBorder,
    transitionTimingFunction: 'var(--ease-in)',
    backgroundColor: transparentize(theme.colors.orange, .2)
  },
  ':active': {
    backgroundColor: transparentize(theme.colors.orange, .4)
  },
  ':focus': {
    outline: 'none',
    boxShadow: `0 0 0 2px ${transparentize(theme.colors.paleOrange, .5)}`
  },
  '.Hug': {
    position: 'relative',
    zIndex: 2
  },
  '::after': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    zIndex: 1,
    backgroundImage: theme.effects.orangeGradient,
    transition: 'opacity .2s',
    transitionTimingFunction: 'var(--ease-out)',
    opacity: 0
  }
}))

const LinkToDocs = styled.a(({ theme }) => ({
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  display: 'inline-block',
  maxWidth: '100%',
  fontSize: 14
}))

export const Aside = () => {
  const [expanded, setExpanded] = useState(false)
  return (
    <Box className="Aside-Box">
      <Container expanded={expanded} onMouseEnter={() => setExpanded(true)} onMouseLeave={() => setExpanded(false)}> {/* the expand/collapse thing with border that works like a drawer */}
        <Hug> {/* the thing that holds buttons */}
          <Hug mb={8}>
            <AsideButton to="/incarnations">
              <Hug as="span" ml={4}>
                <DNA />
              </Hug>
              <Hug as="span" ml={16}>
                Incarnations
              </Hug>
            </AsideButton>
          </Hug>
        </Hug>
        <Hug mt="auto" mb={16}>
          <Hug><LinkToDocs href="https://foxops.readthedocs.io/" target="_blank" rel="noreferrer">Docs</LinkToDocs></Hug>
          <Hug mt={8}><LinkToDocs href="/docs" target="_blank" rel="noreferrer">API Docs</LinkToDocs></Hug>
        </Hug>
      </Container>
    </Box>
  )
}
