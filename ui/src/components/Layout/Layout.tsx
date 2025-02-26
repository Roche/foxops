import styled from '@emotion/styled'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { IncarnationsOperationsWindow } from '../IncarnationsOperationsWindow/IncarnationsOperationsWindow'
import { Aside } from './Aside/Aside'
import { Content } from './Content/Content'
import { Toolbar } from './Toolbar/Toolbar'
import { Hug } from 'components/common/Hug/Hug'
import { useEffect, useState } from 'react'
import { useThemeModeStore } from 'stores/theme-mode'

const Box = styled.div(({ theme }) => ({
  paddingTop: theme.sizes.toolbar,
  paddingLeft: theme.sizes.aside
}))

export type PageConfig = {
  pathMatcher: RegExp;
  title: string;
  description: string;
  breadcrumbs: { label: string; to: string }[];
};

type LayoutProps = {
  config: PageConfig[];
};

const BreadcrumbArrow = styled.span({
  margin: '0 0.5rem',
  textAlign: 'center',
  height: '1rem',
  fontSize: '1rem'
})

const BreadcrumbLink = styled.a({
  color: '#6495ED',
  textDecoration: 'none',
  '&:hover': {
    textDecoration: 'underline'
  },
  cursor: 'pointer',
  fontSize: '1rem',
  height: '1rem',
  fontWeight: 'bold'
})

const BreadcrumSpan = styled.span({
  display: 'inline-block'
})

const PageTitle = styled.h1({
  fontSize: '2rem',
  fontWeight: 'bold',
  margin: '.8rem 0'
})

export const Layout = ({ config }: LayoutProps) => {
  const navigator = useNavigate()
  const location = useLocation()
  const { mode } = useThemeModeStore()
  const [currentConfig, setCurrentConfig] = useState<PageConfig | null>(null)

  useEffect(() => {
    let currentURLConfig
      = config.find(pageConfig => pageConfig.pathMatcher.test(location.pathname)
      ) || null
    if (!currentURLConfig) return
    currentURLConfig = { ...currentURLConfig }

    const match = location.pathname.match(currentURLConfig.pathMatcher || '')

    if (match) {
      Object.entries(match.groups || {}).forEach(([key, value]) => {
        currentURLConfig.description = currentURLConfig.description.replace(`:${key}`, value) || ''
        currentURLConfig.title = currentURLConfig.title.replace(`:${key}`, value) || ''

        currentURLConfig.breadcrumbs = currentURLConfig.breadcrumbs.map(
          breadcrumb => {
            breadcrumb.to = breadcrumb.to.replace(`:${key}`, value)
            breadcrumb.label = breadcrumb.label.replace(`:${key}`, value)
            return breadcrumb
          }
        ) || []
      }
      )
    }
    setCurrentConfig(currentURLConfig)
  }, [config, location.pathname])

  return (
    <Box className="Layout-Box">
      <Toolbar />
      <Aside />
      <Hug>
        <Hug
          w="100%"
          p={8}
          pr={24}
          pl={24}
          h="10rem"
          mah="10rem"
          flex={['aic', 'jcc']}
          style={{ backgroundColor: mode == 'dark' ? '#444444' : '#f5f5f5' }}
        >
          <Hug w="min(90%, 100rem)">
            {currentConfig && (
              <>
                <Hug>
                  {currentConfig.breadcrumbs.map(
                    (breadcrumb, index) => (
                      <BreadcrumSpan key={index}>
                        {index != 0 && <BreadcrumbArrow>{'>'}</BreadcrumbArrow>}
                        <BreadcrumbLink
                          onClick={() => navigator(breadcrumb.to)}
                        >
                          {breadcrumb.label}
                        </BreadcrumbLink>
                      </BreadcrumSpan>
                    )
                  )}
                </Hug>
                <PageTitle>{currentConfig.title}</PageTitle>
                <span>{currentConfig.description}</span>
              </>
            )}
          </Hug>
        </Hug>
        <Hug flex={['aic', 'jcc']} h="calc(100vh - 10rem - 60px)">
          <Content>
            <Outlet />
          </Content>
        </Hug>
      </Hug>
      <IncarnationsOperationsWindow />
    </Box>
  )
}
