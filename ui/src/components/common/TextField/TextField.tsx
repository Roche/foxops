import { Theme } from '@emotion/react'
import styled from '@emotion/styled'
import React, { forwardRef, useId, useState } from 'react'
import { transparentize } from '../../../styling/colors'
import { buildTransform } from '../../../styling/transform'

interface InputComponentProps {
  inputSize: Size,
  hasError: boolean,
}

const sharedStyles = ({ theme, inputSize, hasError }: { theme: Theme } & InputComponentProps) => ({
  border: `1px solid ${hasError ? theme.colors.error : theme.colors.inputBorder}`,
  fontSize: 16,
  padding: '8px',
  width: '100%',
  borderRadius: 4,
  background: theme.colors.baseBg,
  color: theme.colors.text,
  transition: 'box-shadow 0.2s var(--base-easing)',
  height: inputSize === 'large' ? 48 : 38,
  ':focus': {
    outline: 'none',
    boxShadow: hasError ? `0 0 0 2px ${transparentize(theme.colors.error, .4)}` : `0 0 0 2px ${theme.colors.paleOrange}`
  },
  ':disabled': {
    borderStyle: 'dashed',
    color: transparentize(theme.colors.text, .8)
  }
})

const InputComponent = styled.input<InputComponentProps>(sharedStyles)

const Box = styled.div(() => ({
  position: 'relative'
}))

interface LabelProps {
  lifted: boolean,
  size: Size
}

const Label = styled.label<LabelProps>(({ theme, lifted, size }) => {
  const translate = lifted
    ? size === 'large'
      ? { x: 4, y: -24 }
      : { x: 4, y: -19 }
    : undefined
  const scale = lifted ? 0.7 : undefined
  const transform = buildTransform({ translate, scale })
  return {
    position: 'absolute',
    opacity: lifted ? 1 : .7,
    top: size === 'large' ? 15 : 9,
    left: 3,
    transform,
    transition: 'transform 0.15s var(--ease-out)',
    backgroundColor: theme.colors.baseBg,
    paddingLeft: 6,
    paddingRight: 6,
    transformOrigin: '0 50%',
    cursor: 'text',
    color: lifted ? theme.colors.orange : theme.colors.text
  }
})

const Asterisk = styled.span(({ theme }) => ({
  color: theme.colors.error
}))

const InputError = styled.div(({ theme }) => ({
  fontSize: 12,
  color: theme.colors.error,
  marginTop: 4,
  marginBottom: 4
}))

type Size = 'medium' | 'large'
interface TextFieldProps {
  placeholder?: string,
  value?: string,
  onChange?: React.ChangeEventHandler<HTMLInputElement>,
  autoFocus?: boolean,
  type?: 'text' | 'textarea' | 'search',
  defaultValue?: string,
  label?: string,
  name?: string,
  size?: Size,
  testId?: string,
  required?: boolean,
  onFocus?: React.FocusEventHandler<HTMLInputElement>,
  onBlur?: React.FocusEventHandler<HTMLInputElement>,
  error?: string,
  hasError?: boolean,
  disabled?: boolean
}

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(({
  placeholder,
  defaultValue,
  value,
  onChange,
  autoFocus,
  type: _type = 'text',
  label,
  name,
  size = 'medium' as Size,
  testId,
  required,
  onFocus,
  onBlur,
  hasError,
  error,
  ...rest
}, ref) => {
  const type = _type === 'textarea' ? undefined : _type
  const id = useId()
  const [focus, setFocus] = useState(false)
  const _onFocus: React.FocusEventHandler<HTMLInputElement> = e => {
    setFocus(true)
    if (onFocus) {
      onFocus(e)
    }
  }
  const _onBlur:React.FocusEventHandler<HTMLInputElement> = e => {
    setFocus(false)
    if (onBlur) {
      onBlur(e)
    }
  }
  const isControlled = typeof value === 'string' || typeof onChange === 'function'
  const isUncontrolled = !isControlled
  const [hasValue, setHasValue] = useState(!!(isUncontrolled && value || isUncontrolled && defaultValue || false))
  const lifted = hasValue || focus
  const onChangeHandler: React.ChangeEventHandler<HTMLInputElement> = e => {
    setHasValue(!!e.target.value)
    if (onChange) {
      onChange(e)
    }
  }
  return (
    <Box data-testid={testId} >
      {label ? <Label size={size} htmlFor={id} lifted={lifted}>{label} {required ? <Asterisk>*</Asterisk> : null}</Label> : null}
      <InputComponent
        ref={ref}
        data-testid={testId ? `${testId}-Input` : undefined}
        id={id}
        className="TextField-Input"
        type={type}
        defaultValue={defaultValue}
        value={value}
        onChange={onChangeHandler}
        placeholder={placeholder}
        autoFocus={autoFocus}
        onFocus={_onFocus}
        onBlur={_onBlur}
        name={name}
        inputSize={size}
        hasError={!!hasError}
        {...rest} />
      {error ? <InputError>{error}</InputError> : null}
    </Box>
  )
})

TextField.displayName = 'TextField'
