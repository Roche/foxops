import { ButtonLink } from '../../../components/common/Button/Button'
import { Hug } from '../../../components/common/Hug/Hug'
import { Commit } from '../../../components/common/Icons/Commit'
import { MergeRequest } from '../../../components/common/Icons/MergeRequest'
import { Repository } from '../../../components/common/Icons/Repository'
import { Tooltip } from '../../../components/common/Tooltip/Tooltip'
import { IncarnationStatus } from './IncarnationStatus'

interface IncarnationLinksProps {
  mergeRequestUrl?: string | null
  commitUrl?: string
  id?: number
  size?: 'small' | 'large'
  templateRepository?: string | null
}

export const IncarnationLinks = ({
  id,
  commitUrl,
  mergeRequestUrl,
  size = 'small',
  templateRepository
}: IncarnationLinksProps) => {
  const svgProps = size === 'small' ? { width: 16, height: 16 } : { width: 20, height: 20 }
  return (
    <Hug flex={['jcfe', 'aic']}>
      {
        typeof id === 'number' && <IncarnationStatus id={id} size={size} />
      }
      <Tooltip title="Commit" style={{ whiteSpace: 'nowrap' }}>
        <ButtonLink size={size} style={{ maxWidth: 38 }} target="_blank" disabled={!commitUrl} href={commitUrl}>
          <Commit {...svgProps} />
        </ButtonLink>
      </Tooltip>
      <Hug ml={4}>
        <Tooltip title="Merge request" style={{ whiteSpace: 'nowrap' }}>
          <ButtonLink size={size} style={{ maxWidth: 38 }} target="_blank" disabled={!mergeRequestUrl} href={mergeRequestUrl ?? undefined}>
            <MergeRequest {...svgProps} />
          </ButtonLink>
        </Tooltip>
      </Hug>
      {templateRepository && (
        <Hug ml={4}>
          <Tooltip title="Template repository" style={{ whiteSpace: 'nowrap' }}>
            <ButtonLink size={size} href={templateRepository ?? ''} target="_blank">
              <Repository {...svgProps} />
            </ButtonLink>
          </Tooltip>
        </Hug>
      )}
    </Hug>
  )
}
