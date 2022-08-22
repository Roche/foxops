
import { fireEvent, render, screen } from '../../../support/setup-tests'
import { TextField } from './TextField'

test('renders TextField component', () => {
  render(<TextField placeholder="Test" defaultValue="Test" />)
  const textField = screen.getByTestId('TextField')
  expect(textField).toHaveDisplayValue('Test')
  fireEvent.change(textField, { target: { value: 'Test2' } })
  expect(textField).toHaveDisplayValue('Test2')
})
