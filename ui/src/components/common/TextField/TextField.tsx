import { Theme } from '@emotion/react'
import styled from '@emotion/styled'

const sharedStyles = ({ theme }: { theme: Theme }) => ({
  border: `1px solid ${theme.colors.inputBorder}`,
  fontSize: 16,
  padding: '8px',
  width: '100%',
  borderRadius: 4,
  background: theme.colors.baseBg,
  color: theme.colors.text,
  transition: 'box-shadow 0.2s var(--base-easing)',
  ':focus': {
    outline: 'none',
    boxShadow: `0 0 0 2px ${theme.colors.paleOrange}`
  }
})

const InputComponent = styled.input(sharedStyles)
const TextareaComponent = styled.textarea((props: { theme: Theme }) => ({
  ...sharedStyles(props),
  resize: 'vertical'
}))

interface TextFieldProps {
  placeholder?: string,
  value?: string,
  onChange?: React.ChangeEventHandler<HTMLTextAreaElement | HTMLInputElement>,
  autoFocus?: boolean,
  type?: 'text' | 'textarea' | 'search',
  rows?: number,
  defaultValue?: string,
}

export const TextField = ({
  placeholder,
  defaultValue,
  value,
  onChange,
  autoFocus,
  type: _type = 'text',
  rows = 3,
  ...rest
}: TextFieldProps) => {
  const Component = _type === 'textarea' ? TextareaComponent : InputComponent
  const type = _type === 'textarea' ? undefined : _type
  return (
    <Component
      data-testid="TextField"
      rows={rows}
      className="TextField"
      type={type}
      defaultValue={defaultValue}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      autoFocus={autoFocus}
      {...rest} />
  )
}
