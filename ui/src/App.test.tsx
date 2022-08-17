
import { render, screen } from '@testing-library/react'

import App from './App'

test('renders App component', () => {
  render(<App />)
  const title = screen.getByTestId('App-title')
  const subtitle = screen.getByTestId('App-subtitle')
  expect(title).toHaveTextContent('foxops 🦊')
  expect(subtitle).toHaveTextContent('coming soon ...')
})
