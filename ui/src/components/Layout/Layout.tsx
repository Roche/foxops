import styled from '@emotion/styled'
import { Outlet } from 'react-router-dom'
import { Aside } from './Aside/Aside'
import { Content } from './Content/Content'
import { Toolbar } from './Toolbar/Toolbar'

const Box = styled.div({
  display: 'grid',
  height: '100%',
  gridTemplateRows: '60px 1fr',
  gridTemplateColumns: '57px 1fr'
})

export const Layout = () => (
  <Box className="Layout-Box">
    <Toolbar />
    <Aside />
    <Content>
      <Outlet />
    </Content>
  </Box>
)
