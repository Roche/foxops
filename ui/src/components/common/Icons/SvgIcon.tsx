import styled from '@emotion/styled'

const Svg = styled.svg`
  * {
    fill: currentColor;
  }
`
export interface SvgIconProps extends React.SVGAttributes<SVGElement> {
  children: React.ReactNode
}
export const SvgIcon = ({ children, ...props }: SvgIconProps) => (
  <Svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" {...props}>
    {children}
  </Svg>
)
