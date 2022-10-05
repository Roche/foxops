import { useQuery } from '@tanstack/react-query'
import { ErrorTag, StatusTag } from '.'
import { Button, ButtonLink } from '../../../components/common/Button/Button'
import { Hug } from '../../../components/common/Hug/Hug'
import { Commit } from '../../../components/common/Icons/Commit'
import { Download } from '../../../components/common/Icons/Download'
import { MergeRequest } from '../../../components/common/Icons/MergeRequest'
import { Tooltip } from '../../../components/common/Tooltip/Tooltip'
import { incarnations } from '../../../services/incarnations'

interface IncarnationLinksProps {
  mergeRequestUrl?: string | null
  commitUrl?: string
  id?: number,
  size?: 'small' | 'large'
}

export const IncarnationLinks = ({ id, commitUrl, mergeRequestUrl, size = 'small' }: IncarnationLinksProps) => {
  const { data, refetch, isError, isFetching } = useQuery(['incarnations', id], () => incarnations.getById(id), { enabled: false })
  const onGetStatus = () => refetch()
  const svgProps = size === 'small' ? { width: 16, height: 16 } : { width: 20, height: 20 }
  return (
    <Hug flex={['jcfe', 'aic']}>
      {
        typeof id === 'number' && (
          <>
            <Hug mr={4}>
              {isError ? <ErrorTag>error</ErrorTag> : ''}
              {data && !isFetching ? <StatusTag status={data.status} /> : ''}
            </Hug>
            <Hug mr={4}>
              <Tooltip title={isFetching ? 'Getting status...' : 'Get status'}>
                <Button size={size} loading={isFetching} onClick={onGetStatus}>
                  {!isFetching && <Download {...svgProps} />}
                </Button>
              </Tooltip>
            </Hug>
          </>
        )
      }
      <Tooltip title="Commit">
        <ButtonLink size={size} style={{ maxWidth: 38 }} target="_blank" disabled={!commitUrl} href={commitUrl}>
          <Commit {...svgProps} />
        </ButtonLink>
      </Tooltip>
      <Hug ml={4}>
        <Tooltip title="Merge request">
          <ButtonLink size={size} style={{ maxWidth: 38 }} target="_blank" disabled={!mergeRequestUrl} href={mergeRequestUrl ?? undefined}>
            <MergeRequest {...svgProps} />
          </ButtonLink>
        </Tooltip>
      </Hug>
    </Hug>
  )
}
