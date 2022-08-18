import { Global } from '@emotion/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { EnterScreen } from './components/EnterScreen/EnterScreen'
import globalStyles from './global-styles'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Global styles={globalStyles} />
      <EnterScreen />
    </QueryClientProvider>
  )
}

export default App
