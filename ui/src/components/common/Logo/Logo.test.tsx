
import { render, screen } from '@testing-library/react'
import { Logo } from './Logo'

test('renders Logo component', () => {
  render(<Logo />)
  const logo = screen.getByTestId('Logo')
  expect(logo).toHaveTextContent('foxops 🦊')
})
