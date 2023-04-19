import { forwardRef, useId } from 'react'
import styled from '@emotion/styled'

interface ToggleSwitchProps {
  checked: boolean
  onChange: React.ChangeEventHandler<HTMLInputElement>
  label: string
  disabled?: boolean
}

export const ToggleSwitch = forwardRef<HTMLInputElement, ToggleSwitchProps>(({
  checked,
  onChange,
  label,
  disabled,
  ...rest
}, ref) => {
  const id = useId()

  return (
    <Container disabled={disabled}>
      <input
        ref={ref}
        id={id}
        type="checkbox"
        checked={checked}
        onChange={onChange}
        disabled={disabled}
        {...rest} />
      <label
        htmlFor={id}>
        <span className="switch"></span>
        <span>{label}</span>
      </label>
    </Container>
  )
})

ToggleSwitch.displayName = 'ToggleSwitch'

const Container = styled.div<{ disabled?: boolean }>`
  opacity: ${props => props.disabled ? 0.66 : 1};
  input[type=checkbox]{
    display: none;
  }
  label {
    display: inline-flex;
    vertical-align: middle;
    align-items: center;
    gap: 8px;
    .switch {
      cursor: pointer;
      text-indent: -9999px;
      width: 64px;
      height: 32px;
      background: ${props => props.theme.colors.inputBorder};
      display: block;
      border-radius: 100px;
      position: relative;
      transition: background-color 0.3s;
      &::after {
        content: '';
        position: absolute;
        top: 3px;
        left: 3px;
        width: 26px;
        height: 26px;
        background: ${props => props.theme.colors.baseBg};
        border-radius: 26px;
        transition: 0.3s;
      } 
    }
  }
  input:checked + label .switch {
    background: ${props => props.theme.colors.orange};
  }
  input:checked + label .switch::after {
    left: calc(100% - 5px);
    transform: translateX(-100%);
  }
  label:active .switch::after {
    width: 30px;
  }
`
