import { Hug } from '../../common/Hug/Hug'

interface ContentProps {
  children: React.ReactNode
}
export const Content = ({ children, ...rest }: ContentProps) => (
  <Hug p={16} className="Content-Hug" {...rest}>
    {children}
  </Hug>
)
