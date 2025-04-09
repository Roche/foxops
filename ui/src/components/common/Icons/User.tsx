import { FALicense } from './FALicense'
import { SvgIcon, SvgIconProps } from './SvgIcon'

export const User = (props: Partial<SvgIconProps>) => (
  <SvgIcon {...props} viewBox="0 0 448 512">
    <FALicense />
    <path d="M224 256A128 128 0 1 0 224 0a128 128 0 1 0 0 256zm-45.7 48C79.8 304 0 383.8 0 482.3C0 498.7 13.3 512 29.7 512l388.6 0c16.4 0 29.7-13.3 29.7-29.7C448 383.8 368.2 304 269.7 304l-91.4 0z"/>
  </SvgIcon>
)
