import styled from '@emotion/styled'

interface LogoProps {
  size?: null | string | number
}

const Component = styled('div', { shouldForwardProp: prop => prop !== 'size' })(
  ({ size }: LogoProps) => ({
    fontSize: size ?? 24,
    fontWeight: 700
  })
)

export const Logo = ({
  size,
  ...props
}: LogoProps) => (
  <Component data-testid="Logo" size={size} {...props}>foxops 🦊</Component>
)
