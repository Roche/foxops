import { Global, ThemeProvider } from '@emotion/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { EnterScreen } from './components/EnterScreen/EnterScreen'
import { Login } from './routes/login/Login'
import { createGlobalStyles } from './global-styles'
import { useThemeModeStore } from './stores/theme-mode'
import { THEMES } from './styling/themes'
import { CreateIncarnationForm } from './routes/incarnations/CreateForm'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { EditIncarnationForm } from './routes/incarnations/EditForm'
import { BulkUpdateIncarnations } from './routes/incarnations/BulkUpdate'
import { IncarnationsTable } from './routes/incarnations/Table/Table'
import { DiffIncarnation } from './routes/incarnations/DiffIncarnation'
import './hooks/use-worker'
import { PageConfig } from 'components/Layout/Layout'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 0
    }
  }
})

const pageConfigs: Array<PageConfig> = [
  {
    pathMatcher: /^\/incarnations$/,
    title: 'Incarnations',
    description: 'List of all available incarnations',
    breadcrumbs: [{ label: 'Incarnations', to: '/incarnations' }]
  },
  {
    pathMatcher: /^\/incarnations\/create$/,
    title: 'Create Incarnation',
    description: 'Create a new incarnation',
    breadcrumbs: [
      { label: 'Incarnations', to: '/incarnations' },
      { label: 'Create', to: '/incarnations/create' }
    ]
  },
  {
    pathMatcher: /^\/incarnations\/bulk-update$/,
    title: 'Bulk Update Incarnations',
    description: 'Bulk update incarnations',
    breadcrumbs: [
      { label: 'Incarnations', to: '/incarnations' },
      { label: 'Bulk Update', to: '/incarnations/bulk-update' }
    ]
  },
  {
    pathMatcher: /^\/incarnations\/(?<id>\d+)$/,
    title: 'Edit Incarnation',
    description: 'You are currently editing the incarnation with the id :id',
    breadcrumbs: [
      { label: 'Incarnations', to: '/incarnations' },
      { label: 'Edit', to: '/incarnations/:id' }
    ]
  },
  {
    pathMatcher: /^\/incarnations\/(?<id>\d+)\/diff$/,
    title: 'Diff Incarnation',
    description:
      'The following diff shows all the changes, which where manually made to the incernation with the id :id. Those changes are not tracked by foxops and will not be rendered if the incarnation is recreated',
    breadcrumbs: [
      { label: 'Incarnations', to: '/incarnations' },
      {
        label: 'Edit',
        to: '/incarnations/:id'
      },
      { label: 'Diff', to: '/incarnations/:id/diff' }
    ]
  }
]

function App() {
  const { mode } = useThemeModeStore()
  const theme = THEMES[mode]
  const globalStyles = createGlobalStyles(theme, mode)

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <Global styles={globalStyles} />
        <BrowserRouter>
          <Routes>
            <Route path="*" element={<EnterScreen config={pageConfigs} />}>
              <Route path="incarnations" element={<IncarnationsTable />} />
              <Route
                path="incarnations/create"
                element={<CreateIncarnationForm />}
              />
              <Route
                path="incarnations/bulk-update"
                element={<BulkUpdateIncarnations />}
              />
              <Route
                path="incarnations/:id"
                element={<EditIncarnationForm />}
              />
              <Route
                path="incarnations/:id/diff"
                element={<DiffIncarnation />}
              />
              <Route path="*" element={<Navigate to="/incarnations" />} />
            </Route>
            <Route path="/login" element={<Login />} />
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
      <ReactQueryDevtools position="bottom-left" />
    </QueryClientProvider>
  )
}

export default App
