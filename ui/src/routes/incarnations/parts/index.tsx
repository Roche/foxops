import styled from '@emotion/styled'
import { forwardRef } from 'react'
import { transparentize } from '../../../styling/colors'
import { MergeRequestStatus } from '../../../interfaces/incarnations.types'

export const Section = styled.div({
  maxWidth: '100%',
  margin: '0 auto',
  position: 'relative',
  height: '100%'
})

interface StatusProps {
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
const Status = styled.div<StatusProps>(({ theme, mergeRequestStatus }) => {
  let color = theme.colors.statusUnknown
  switch (mergeRequestStatus) {
    case 'unknown':
      color = theme.colors.statusUnknown
      break
    case 'merged':
    case 'open':
      color = theme.colors.statusSuccess
      break
    case 'closed':
      color = theme.colors.statusPending
      break
    default:
      break
  }
  return createTagStyle(color)
})

interface StatusTagProps {
  mergeRequestStatus: MergeRequestStatus | null
}

export const StatusTag = forwardRef<HTMLDivElement, StatusTagProps>(({ mergeRequestStatus, ...rest }, ref) => (
  <Status
    mergeRequestStatus={mergeRequestStatus}
    ref={ref}
    {...rest}>
    {mergeRequestStatus ?? 'no MR'}
  </Status>
))

StatusTag.displayName = 'StatusTag'

export const ErrorTag = styled.div(({ theme }) => createTagStyle(theme.colors.statusFailure))
