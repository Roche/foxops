import { SvgIcon, SvgIconProps } from './SvgIcon'

export const Minus = (props: Partial<SvgIconProps>) => (
  <SvgIcon {...props}>
    <path d="M18 12L6 12" stroke="currentColor" strokeWidth={2} strokeLinecap="round"/>
  </SvgIcon>
)
