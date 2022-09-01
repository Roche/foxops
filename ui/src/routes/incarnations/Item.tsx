import { Commit } from '../../components/common/Icons/Commit'
import { MergeRequest } from '../../components/common/Icons/MergeRequest'
import { Tooltip } from '../../components/common/Tooltip/Tooltip'
import { Download } from '../../components/common/Icons/Download'
import { IncarnationBase, incarnations, IncarnationStatus } from '../../services/incarnations'
import styled from '@emotion/styled'
import { Hug } from '../../components/common/Hug/Hug'
import { Button, ButtonLink } from '../../components/common/Button/Button'
import { useQuery } from '@tanstack/react-query'
import { transparentize } from '../../styling/colors'

const CellText = styled.div({
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  maxWidth: '100%'
})

interface IncarnationItemProps {
  incarnation: IncarnationBase
}

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

const StatusTag = ({ status }: { status: IncarnationStatus }) => (
  <Status type={status}>{status}</Status>
)

const ErrorTag = styled.div(({ theme }) => createTagStyle(theme.colors.statusFailure))

export const IncarnationItem = ({ incarnation }: IncarnationItemProps) => {
  const { id, commitUrl, mergeRequestUrl, incarnationRepository, targetDirectory } = incarnation
  const { data, refetch, isError, isFetching } = useQuery(['incarnations', id], () => incarnations.getById(id), { enabled: false })
  const onGetStatus = () => refetch()
  return (
    <tr key={id}>
      <td>{id}</td>
      <td>
        <Tooltip title={incarnationRepository} placement="bottom-start">
          <CellText>{incarnationRepository}</CellText>
        </Tooltip>
      </td>
      <td>
        <Tooltip title={targetDirectory} placement="bottom-start">
          <CellText>{targetDirectory}</CellText>
        </Tooltip>
      </td>
      <td>
        <Hug flex={['jcfe', 'aic']}>
          <Hug mr={4}>
            {isError ? <ErrorTag>error</ErrorTag> : ''}
            {data && !isFetching ? <StatusTag status={data.status} /> : ''}
          </Hug>
          <Hug mr={4}>
            <Tooltip title={isFetching ? 'Getting status...' : 'Get status'}>
              <Button size="small" loading={isFetching} onClick={onGetStatus}>
                {!isFetching && <Download />}
              </Button>
            </Tooltip>
          </Hug>
          <Tooltip title="Commit">
            <ButtonLink size="small" target="_blank" disabled={!commitUrl} href={commitUrl}>
              <Commit />
            </ButtonLink>
          </Tooltip>
          <Hug ml={4}>
            <Tooltip title="Merge request">
              <ButtonLink size="small" target="_blank" disabled={!mergeRequestUrl} href={mergeRequestUrl ?? undefined}>
                <MergeRequest />
              </ButtonLink>
            </Tooltip>
          </Hug>
        </Hug>
      </td>
    </tr>
  )
}
