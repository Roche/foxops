import styled from '@emotion/styled'
import clsx from 'clsx'

export const ResizerComponent = styled.div`
  position: absolute;
  right: -2px;
  top: 0;
  height: 100%;
  width: 5px;
  cursor: col-resize;
  user-select: none;
  touch-action: none;
  opacity: 0;
  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 2px;
    width: 1px;
    height: 100%;
    background: var(--grey-200);
  }
  &.is-resizing {
    background: var(--orange-500);
    opacity: 1;
  }
  *:hover > & {
    opacity: 1;
  }
`

export interface ResizerProps extends React.HTMLAttributes<HTMLDivElement> {
  isResizing: boolean
}
export const Resizer = ({ isResizing, ...props }: ResizerProps) => (
  <ResizerComponent
    className={
      clsx(
        'resizer',
        isResizing && 'is-resizing'
      )
    }
    {...props} />
)
