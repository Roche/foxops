import { forwardRef, useId } from 'react'
import styled from '@emotion/styled'

interface ToggleSwitchProps {
  checked: boolean
  onChange: React.ChangeEventHandler<HTMLInputElement>
  label: string
  disabled?: boolean,
  size?: 'small' | 'medium'
}

export const ToggleSwitch = forwardRef<HTMLInputElement, ToggleSwitchProps>(({
  checked,
  onChange,
  label,
  disabled,
  size = 'medium',
  ...rest
}, ref) => {
  const id = useId()
  return (
    <Container
      small={size === 'small'}
      disabled={disabled}>
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

const Container = styled.div<{ disabled?: boolean, small: boolean }>`
  --size: ${x => x.small ? 22 : 32}px;
  --circle-size: ${x => x.small ? 16 : 26}px;
  --circle-offset: calc((var(--size) - var(--circle-size)) / 2);
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
      width: calc(var(--size) * 2);
      height: var(--size);
      background: ${props => props.theme.colors.inputBorder};
      display: block;
      border-radius: 100px;
      position: relative;
      transition: background-color 0.3s;
      &::after {
        content: '';
        position: absolute;
        top: var(--circle-offset);
        left: var(--circle-offset);
        width: var(--circle-size);
        height: var(--circle-size);
        background: var(--base-bg);
        border-radius: var(--circle-size);
        transition: 0.3s;
      } 
    }
  }
  input:checked + label .switch {
    background: var(--primary);
  }
  input:checked + label .switch::after {
    transform: translateX(calc(var(--size)));
  }
  label:active .switch::after {
    /* width: calc(var(--circle-size) + var(--circle-offset)); */
  }
  .off-label {
    margin-right: 8px;
  }
`
