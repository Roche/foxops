import { ButtonLink } from '../../../components/common/Button/Button'
import { Hug } from '../../../components/common/Hug/Hug'
import { Commit } from '../../../components/common/Icons/Commit'
import { MergeRequest } from '../../../components/common/Icons/MergeRequest'
import { Tooltip } from '../../../components/common/Tooltip/Tooltip'
import { IncarnationStatus } from './IncarnationStatus'

interface IncarnationLinksProps {
  mergeRequestUrl?: string | null
  commitUrl?: string
  id?: number,
  size?: 'small' | 'large'
}

export const IncarnationLinks = ({ id, commitUrl, mergeRequestUrl, size = 'small' }: IncarnationLinksProps) => {
  const svgProps = size === 'small' ? { width: 16, height: 16 } : { width: 20, height: 20 }
  return (
    <Hug flex={['jcfe', 'aic']}>
      {
        typeof id === 'number' && <IncarnationStatus id={id} size={size} />
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
