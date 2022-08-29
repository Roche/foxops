
import { THEMES } from '../../../styling/themes'
import { render, screen } from '../../../support/setup-tests'
import { DarkMode } from '../Icons/DarkMode'
import { IconButton } from './IconButton'

const { colors } = THEMES.light
test('renders IconButton component with some svg inside', () => {
  render(<IconButton data-testid="IconButton"><DarkMode /></IconButton>)
  const iconButton = screen.getByTestId('IconButton')
  expect(iconButton.querySelector('svg')).toBeDefined()
  expect(iconButton).toHaveStyle({ color: colors.iconButtonColor, borderColor: colors.iconButtonBorder })
})

test('renders IconButton component in its active state', () => {
  render(<IconButton data-testid="IconButton" active><DarkMode /></IconButton>)
  const iconButton = screen.getByTestId('IconButton')
  expect(iconButton).toHaveStyle({ color: colors.textContrast })
})

test('renders IconButton component in its flying state (no border)', () => {
  render(<IconButton data-testid="IconButton" flying><DarkMode /></IconButton>)
  const iconButton = screen.getByTestId('IconButton')
  expect(iconButton).toHaveStyle({ border: 'none' })
})
