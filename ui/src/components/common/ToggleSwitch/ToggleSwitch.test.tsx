
import { useState } from 'react'
import { fireEvent, render, screen } from '../../../support/setup-tests'
import { ToggleSwitch } from './ToggleSwitch'

const Switch = () => {
  const [value, setValue] = useState(false)
  return (
    <ToggleSwitch
      label="Test"
      checked={value}
      onChange={() => setValue(!value)}
    />
  )
}

test('renders ToggleSwitch component', () => {
  render(<Switch />)
  const label = screen.getByText('Test').closest('label')
  if (!label) throw new Error('ToggleSwitch label not found')
  expect(label.previousElementSibling).not.toBeChecked()
  fireEvent.click(label)
  expect(label.previousElementSibling).toBeChecked()
})
