
import { render, screen } from '../../../support/setup-tests'
import { FloatingActionButton } from './FloatingActionButton'

test('renders FloatingActionButton component', () => {
  render(<FloatingActionButton data-testid="FloatingActionButton" />)
  const button = screen.getByTestId('FloatingActionButton')
  expect(button.querySelector('svg')).toBeDefined()
})
