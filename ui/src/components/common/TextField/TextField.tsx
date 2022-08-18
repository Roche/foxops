import styled from '@emotion/styled'

const sharedStyles = {
  border: '1px solid var(--grey)',
  fontSize: 16,
  padding: '8px',
  width: '100%',
  borderRadius: 4,
  background: '#fff',
  transition: 'box-shadow 0.2s var(--easing)',
  ':focus': {
    outline: 'none',
    boxShadow: '0 0 0 2px var(--pale-orange)'
  }
}

const InputComponent = styled.input(sharedStyles)
const TextareaComponent = styled.textarea({
  ...sharedStyles,
  resize: 'vertical'
})

interface TextFieldProps {
  placeholder?: string,
  value?: string,
  onChange?: React.ChangeEventHandler<HTMLTextAreaElement | HTMLInputElement>,
  autoFocus?: boolean,
  type?: 'text' | 'textarea',
  rows?: number,
  defaultValue?: string,
}

export const TextField = ({
  placeholder,
  defaultValue,
  value,
  onChange,
  autoFocus,
  type = 'text',
  rows = 3,
  ...rest
}: TextFieldProps) => {
  const Component = type === 'textarea' ? TextareaComponent : InputComponent
  return (
    <Component
      data-testid="TextField"
      rows={rows}
      className="TextField"
      type="text"
      defaultValue={defaultValue}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      autoFocus={autoFocus}
      {...rest} />
  )
}
