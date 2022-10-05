import { Tooltip } from '../../components/common/Tooltip/Tooltip'
import { IncarnationBase } from '../../services/incarnations'
import styled, { CSSObject } from '@emotion/styled'
import { Link } from 'react-router-dom'
import { IncarnationLinks } from './parts/IncarnationLinks'

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
  const { id, incarnationRepository, targetDirectory } = incarnation
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
        <IncarnationLinks
          id={incarnation.id}
          commitUrl={incarnation.commitUrl}
          mergeRequestUrl={incarnation.mergeRequestUrl} />
      </td>
    </tr>
  )
}
