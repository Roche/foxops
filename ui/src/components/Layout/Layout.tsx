import styled from '@emotion/styled'
import { Outlet } from 'react-router-dom'
import { Aside } from './Aside/Aside'
import { Content } from './Content/Content'
import { Toolbar } from './Toolbar/Toolbar'

const Box = styled.div(({ theme }) => ({
  paddingTop: theme.sizes.toolbar,
  paddingLeft: theme.sizes.aside
}))

export const Layout = () => (
  <Box className="Layout-Box">
    <Toolbar />
    <Aside />
    <Content>
      <Outlet />
    </Content>
  </Box>
)
