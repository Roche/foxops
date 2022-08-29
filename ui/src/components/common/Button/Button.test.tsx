
import { render, screen } from '../../../support/setup-tests'
import { Button, ButtonLink } from './Button'

test('renders Button component', () => {
  render(<Button dataTestid="Test-Button">Test button</Button>)
  const button = screen.getByTestId('Test-Button')
  expect(button).toHaveTextContent('Test button')
})

test('renders ButtonLink component', () => {
  render(<ButtonLink dataTestid="Test-ButtonLink" href="#" target="_blank">Test button link</ButtonLink>)
  const link = screen.getByTestId('Test-ButtonLink')
  expect(link).toHaveTextContent('Test button link')
  expect(link.getAttribute('href')).toBe('#')
  expect(link.getAttribute('target')).toBe('_blank')
})
