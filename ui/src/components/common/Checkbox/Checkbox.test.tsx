import { render, screen } from 'support/setup-tests'
import { Checkbox } from './Checkbox'
import { useState } from 'react'
import userEvent from '@testing-library/user-event'

const CheckboxControl = ({ disabled = false }) => {
  const [checked, setChecked] = useState(false)
  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setChecked(e.target.checked)
  }
  return (
    <Checkbox
      disabled={disabled}
      checked={checked}
      label={checked ? 'Checked' : 'Some label'}
      onChange={onChange} />
  )
}

test('renders CheckBox', async () => {
  render(<CheckboxControl />)
  expect(screen.getByText('Some label')).toBeInTheDocument()
})

test('changes CheckBox state', async () => {
  render(<CheckboxControl />)
  const user = userEvent.setup()
  expect(screen.getByText('Some label')).toBeInTheDocument()
  await user.click(screen.getByText('Some label'))
  expect(screen.getByText('Checked')).toBeInTheDocument()
})

test('renders disabled input', async () => {
  render(<CheckboxControl disabled />)
  // const user = userEvent.setup()
  expect(screen.getByLabelText('Some label')).toBeDisabled()
})
