import styled from '@emotion/styled'
import { forwardRef } from 'react'
import { IncarnationStatus } from '../../../services/incarnations'
import { transparentize } from '../../../styling/colors'

export const Section = styled.div({
  maxWidth: 'calc(100% - 120px)',
  margin: '0 auto',
  padding: 8,
  position: 'relative'
})

interface StatusProps {
  type: IncarnationStatus
}
const createTagStyle = (color: string) => ({
  fontSize: 12,
  padding: '4px 6px',
  color,
  borderRadius: 6,
  background: transparentize(color, 0.05),
  border: `1px solid ${color}`
})
const Status = styled.div<StatusProps>(({ theme, type }) => {
  let color = theme.colors.statusSuccess
  switch (type) {
    case 'pending':
      color = theme.colors.statusPending
      break
    case 'unknown':
      color = theme.colors.statusUnknown
      break
    case 'failed':
      color = theme.colors.statusFailure
      break
    default:
      break
  }
  return createTagStyle(color)
})

interface StatusTagProps {
  status: IncarnationStatus
}

export const StatusTag = forwardRef<HTMLDivElement, StatusTagProps>(({ status, ...rest }, ref) => (
  <Status type={status} ref={ref} {...rest}>{status}</Status>
))

StatusTag.displayName = 'StatusTag'

export const ErrorTag = styled.div(({ theme }) => createTagStyle(theme.colors.statusFailure))
