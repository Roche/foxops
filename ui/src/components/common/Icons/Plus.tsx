import { SvgIcon, SvgIconProps } from './SvgIcon'

export const Plus = (props: Partial<SvgIconProps>) => (
  <SvgIcon {...props}>
    <path d="M12 6L12 18" stroke="currentColor" strokeWidth={2} strokeLinecap="round"/>
    <path d="M18 12L6 12" stroke="currentColor" strokeWidth={2} strokeLinecap="round"/>
  </SvgIcon>
)
