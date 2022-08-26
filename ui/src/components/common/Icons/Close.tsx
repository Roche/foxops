import { SvgIcon, SvgIconProps } from './SvgIcon'

export const Close = (props: Partial<SvgIconProps>) => (
  <SvgIcon {...props}>
    <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </SvgIcon>
)
