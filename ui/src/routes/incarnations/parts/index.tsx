import styled from '@emotion/styled'
import { forwardRef } from 'react'
import { IncarnationStatus, MergeRequestStatus } from '../../../services/incarnations'
import { transparentize } from '../../../styling/colors'

export const Section = styled.div({
  maxWidth: 1200,
  margin: '0 auto',
  padding: 8,
  position: 'relative'
})

interface StatusProps {
  status: IncarnationStatus
  mergeRequestStatus: MergeRequestStatus | null
}
const createTagStyle = (color: string) => ({
  width: 65,
  textAlign: 'center' as const,
  fontSize: 12,
  padding: '4px 6px',
  color,
  borderRadius: 6,
  background: transparentize(color, 0.05),
  border: `1px solid ${color}`
})
const Status = styled.div<StatusProps>(({ theme, status, mergeRequestStatus }) => {
  let color = theme.colors.statusSuccess
  if (mergeRequestStatus) {
    switch (mergeRequestStatus) {
      case 'unknown':
        color = theme.colors.statusUnknown
        break
      case 'merged':
        color = theme.colors.statusSuccess
        break
      case 'closed':
        color = theme.colors.statusPending
        break
      default:
        break
    }
    return createTagStyle(color)
  }
  switch (status) {
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
  mergeRequestStatus: MergeRequestStatus | null
}

export const StatusTag = forwardRef<HTMLDivElement, StatusTagProps>(({ status, mergeRequestStatus, ...rest }, ref) => (
  <Status
    status={status}
    mergeRequestStatus={mergeRequestStatus}
    ref={ref}
    {...rest}>
    {mergeRequestStatus || status}
  </Status>
))

StatusTag.displayName = 'StatusTag'

export const ErrorTag = styled.div(({ theme }) => createTagStyle(theme.colors.statusFailure))
