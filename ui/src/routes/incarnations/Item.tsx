import { Commit } from '../../components/common/Icons/Commit'
import { MergeRequest } from '../../components/common/Icons/MergeRequest'
import { Tooltip } from '../../components/common/Tooltip/Tooltip'
import { Download } from '../../components/common/Icons/Download'
import { IncarnationBase, incarnations } from '../../services/incarnations'
import styled, { CSSObject } from '@emotion/styled'
import { Hug } from '../../components/common/Hug/Hug'
import { Button, ButtonLink } from '../../components/common/Button/Button'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ErrorTag, StatusTag } from './parts'

const sharedStyles: CSSObject = {
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  maxWidth: '100%'
}

const CellText = styled.div(sharedStyles)

const CellLink = styled(Link)({
  ...sharedStyles,
  display: 'block',
  textDecoration: 'none',
  ':hover': {
    textDecoration: 'underline'
  }
})

interface IncarnationItemProps {
  incarnation: IncarnationBase
}

export const IncarnationItem = ({ incarnation }: IncarnationItemProps) => {
  const { id, commitUrl, mergeRequestUrl, incarnationRepository, targetDirectory } = incarnation
  const { data, refetch, isError, isFetching } = useQuery(['incarnations', id], () => incarnations.getById(id), { enabled: false })
  const onGetStatus = () => refetch()
  return (
    <tr key={id}>
      <td>{id}</td>
      <td>
        <Tooltip title={incarnationRepository} placement="bottom-start">
          <CellLink to={`${id}`}>{incarnationRepository}</CellLink>
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
