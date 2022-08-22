
import { render, screen } from '../../../support/setup-tests'
import { Logo } from './Logo'

test('renders Logo component', () => {
  render(<Logo />)
  const logo = screen.getByTestId('Logo')
  expect(logo).toHaveTextContent('foxops 🦊')
})
