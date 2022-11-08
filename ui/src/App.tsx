import { Global, ThemeProvider } from '@emotion/react'
import { QueryClient, QueryClientProvider, QueryCache } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import toast, { Toaster } from 'react-hot-toast'
import { EnterScreen } from './components/EnterScreen/EnterScreen'
import { IncarnationsList } from './routes/incarnations/List'
import { Login } from './routes/login/Login'
import { createGlobalStyles } from './global-styles'
import { useThemeModeStore } from './stores/theme-mode'
import { THEMES } from './styling/themes'
import { CreateIncarnationForm } from './routes/incarnations/CreateForm'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { EditIncarnationForm } from './routes/incarnations/EditForm'
import { AuthError } from './services/api'

const authError = (err: AuthError) => {
  toast.error(
    <div>
      <b>Authorization Error</b><br />
    (<i>{err.detail}</i>)<br /><br />
    Please logout and login again<br />
    </div>,
    {
      duration: 5000
    }
  )
}

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: error => {
      const auth_error = (error as AuthError)
      if (auth_error.status === 401) authError(auth_error)
    }
  })
})

function App() {
  const { mode } = useThemeModeStore()
  const theme = THEMES[mode]
  const globalStyles = createGlobalStyles(theme)
  return (
    <>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <Global styles={globalStyles} />
          <BrowserRouter>
            <Routes>
              <Route path="*" element={<EnterScreen />}>
                <Route path="incarnations" element={<IncarnationsList />} />
                <Route path="incarnations/create" element={<CreateIncarnationForm />} />
                <Route path="incarnations/:id" element={<EditIncarnationForm />} />
                <Route path="*" element={<Navigate to="/incarnations" />} />
              </Route>
              <Route path="/login" element={<Login />} />
            </Routes>
          </BrowserRouter>
        </ThemeProvider>
        <ReactQueryDevtools position="bottom-right" />
      </QueryClientProvider>
      <Toaster position="top-center" reverseOrder={true} />
    </>
  )
}

export default App
