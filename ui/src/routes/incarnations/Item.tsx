import { Tooltip } from '../../components/common/Tooltip/Tooltip'
import { Incarnation, IncarnationBase } from '../../services/incarnations'
import styled, { CSSObject } from '@emotion/styled'
import { Link } from 'react-router-dom'
import { IncarnationLinks } from './parts/IncarnationLinks'
import { Hug } from '../../components/common/Hug/Hug'
import { useCanShowVersionStore } from '../../stores/show-version'
import { useQueryClient } from '@tanstack/react-query'

const Row = styled(Hug)(({ theme }) => ({
  borderBottom: `1px solid ${theme.colors.grey}`
}))

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
  isScrolling: boolean
}

export const IncarnationItem = ({ incarnation, isScrolling }: IncarnationItemProps) => {
  const { id, incarnationRepository, targetDirectory } = incarnation
  const { canShow } = useCanShowVersionStore()
  const queryClient = useQueryClient()
  const cached = queryClient.getQueryData<Incarnation>(['incarnations', id])

  return (
    <Row flex key={incarnation.id} h={41}>
      <Hug flex={['aic', 'jcc']} allw={50} py={4} px={8}>{id}</Hug>
      <Hug
        allw={`calc(100% - 50px - 280px - 218px${canShow ? ' - 200px' : ''})`}
        flex={['aic']}
        py={4} px={8}>
        <Tooltip title={incarnationRepository} placement="bottom-start">
          <CellLink to={`${id}`}>{incarnationRepository}</CellLink>
        </Tooltip>
      </Hug>
      <Hug flex={['aic']} allw="280px" py={4} px={8}>
        <Tooltip title={targetDirectory} placement="bottom-start">
          <CellText>{targetDirectory}</CellText>
        </Tooltip>
      </Hug>
      {canShow && (
        <Hug flex={['aic']} allw={200} py={4} px={8}>
          <Tooltip title={cached?.templateRepositoryVersion} placement="bottom-start">
            <CellText>{cached?.templateRepositoryVersion}</CellText>
          </Tooltip>
        </Hug>
      )}
      {!isScrolling && <Hug flex={['aic', 'jcfe']} py={4} allw="218px" px={8}>
        <IncarnationLinks
          id={incarnation.id}
          commitUrl={incarnation.commitUrl}
          mergeRequestUrl={incarnation.mergeRequestUrl} />
      </Hug>}
    </Row>
  )
}
