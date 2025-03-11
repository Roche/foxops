import styled from '@emotion/styled'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { IncarnationsOperationsWindow } from '../IncarnationsOperationsWindow/IncarnationsOperationsWindow'
import { Aside } from './Aside/Aside'
import { Content } from './Content/Content'
import { Toolbar } from './Toolbar/Toolbar'
import { Hug } from 'components/common/Hug/Hug'
import { useEffect, useState } from 'react'
import { useThemeModeStore } from 'stores/theme-mode'
import { useErrorStore } from 'stores/error'
import DOMPurify from 'dompurify'
import { IconButton } from '../../components/common/IconButton/IconButton'
import { Close } from 'components/common/Icons/Close'

const Box = styled.div(({ theme }) => ({
  paddingTop: theme.sizes.toolbar,
  paddingLeft: theme.sizes.aside
}))

const ErrorMessage = styled.div(({ theme }) => ({
  color: theme.colors.contrastText,
  fontFamily: 'var(--monospace)',
  background: theme.colors.error,
  fontSize: 14,
  borderRadius: 4,
  lineHeight: 1.5,
  minHeight: '4rem',
  '.IconButton--Error': {
    color: theme.colors.contrastText,
    float: 'right'
  },
  width: 'min(25rem, 80%)'
}))

const ErrorText = styled.div({
  paddingTop: 10
})

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

const ErrorWrapper = styled.div({
  width: '100vw',
  height: '100vh',
  position: 'fixed',
  top: 0,
  left: 0,
  paddingTop: '6rem',
  display: 'flex',
  alignItems: 'start',
  justifyContent: 'right',
  paddingRight: '1rem'
})

const LoadbarWrapper = styled.div({
  width: '100%',
  height: '.25rem',
  background: '#ffffff70'
})

const Loadbar = styled.div(() => ({
  width: '30%',
  height: '100%',
  background: '#ffffffdd',
  animation: 'loadbar 15s linear forwards'
}))

const ErrorBody = styled.div({
  width: '100%',
  padding: '1rem'
})

export const Layout = ({ config }: LayoutProps) => {
  const navigator = useNavigate()
  const location = useLocation()
  const { mode } = useThemeModeStore()
  const errorStore = useErrorStore()

  console.log('config', errorStore.error)

  const [currentConfig, setCurrentConfig] = useState<PageConfig | null>(null)
  const [inErrorCloseProcess, setInCloseProcess] = useState(false)

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
      {errorStore.error ? (
        <ErrorWrapper style={{ animation: inErrorCloseProcess ? 'error-close 0.5s' : '' }} onAnimationEnd={() => {
          errorStore.clearError()
          setInCloseProcess(false)
        }}>
          <ErrorMessage>
            <ErrorBody>
              <IconButton
                flying
                onClick={() => errorStore.clearError()}
                className="IconButton--Error"
              >
                <Close />
              </IconButton>
              <ErrorText>{errorStore.error.message}</ErrorText>
              <Hug>
                {errorStore.error.documentation ? (
                  <a
                    href={DOMPurify.sanitize(errorStore.error.documentation)}
                    target="_blank"
                    rel="noreferrer"
                  >
                        Read more
                  </a>
                ) : null}
              </Hug>
            </ErrorBody>
            <LoadbarWrapper>
              <Loadbar onAnimationEnd={e => {
                e.stopPropagation()
                setInCloseProcess(true)
              }} />
            </LoadbarWrapper>
          </ErrorMessage>
        </ErrorWrapper>
      ) : null}
    </Box>
  )
}
