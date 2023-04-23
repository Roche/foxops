import styled from '@emotion/styled'
import { useId } from 'react'

interface CheckboxProps {
  checked: boolean
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  label: string,
  disabled?: boolean
  name?: string
}
export const Checkbox = ({
  checked,
  onChange,
  label,
  disabled,
  name
}: CheckboxProps) => {
  const id = useId()
  return (
    <Box>
      <input disabled={disabled} id={id} name={name} type="checkbox" checked={checked} onChange={onChange} />
      <span className="checkbox">
        <svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M4 8L6.5 10.5L12 4" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
      <label htmlFor={id}>{label}</label>
    </Box>
  )
}

const Box = styled.div`
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  label {
    cursor: pointer;
    user-select: none;
  }
  &:hover {
    input:not(:disabled) ~ label {
      color: var(--grey-700);
    }
  }
  input {
    display: none;
  }
  .checkbox {
    display: flex;
    justify-content: center;
    width: 16px;
    height: 16px;
    background-color: var(--grey-100);
    border-radius: 4px;
    svg {
      opacity: 0;
      margin-top: 2px;
    }
  }
  input:checked {
    + .checkbox {
      background-color: var(--primary);
      svg {
        opacity: 1;
      }
    }
  }
  input:disabled {
    + .checkbox {
      background-color: var(--grey-200);
    }
    ~ label {
      color: var(--grey-400);
    }
  }
`
