import styled from '@emotion/styled'
import { Link } from 'react-router-dom'
import { useIncarnationsOperations } from '../../stores/incarnations-operations'
import { Button } from '../common/Button/Button'
import { Divider } from '../common/Divider/Divider'
import { Hug } from '../common/Hug/Hug'
import { Bulk } from '../common/Icons/Bulk'
import { Close } from '../common/Icons/Close'

const Container = styled.div`
  position: fixed;
  bottom: 0;
  left: 0;
  z-index: 5;
`

const Box = styled.div<{show: boolean}>`
  position: absolute;
  bottom: 0;
  left: 73px;
  width: 460px;
  transform: translateY(${x => x.show ? '0' : '100%'});
  border-radius: 4px 4px 0 0;
  overflow: hidden;
  transition:
    transform 0.2s var(${x => x.show ? '--ease-in' : '--ease-out'}),
    height 0.2s var(${x => x.show ? '--ease-in' : '--ease-out'});
  box-shadow: ${x => x.theme.effects.incarnationOperationWindowShadow};
`

const Header = styled.div`
  background-color: ${x => x.theme.colors.baseBg};
  color: ${x => x.theme.colors.text};
  min-height: 56px;
  padding: 8px 16px;
`

export const IncarnationsOperationsWindow = () => {
  const { selectedIncarnations, clearAll, updatingIds, updatedIds, failedUpdatedIds } = useIncarnationsOperations()
  const { length } = selectedIncarnations
  const show = !!length
  const showProgress = !!updatingIds.length || !!updatedIds.length || !!failedUpdatedIds.length
  const progressContent = (
    <Hug>
      <Hug mx={-16} my={8}>
        <Divider />
      </Hug>
      <Hug mb={8}>Successfully updated {updatedIds.length}/{updatingIds.length} incarnation{updatingIds.length !== 1 ? 's' : ''}</Hug>
      <Hug>Failed {failedUpdatedIds.length} update{failedUpdatedIds.length !== 1 ? 's' : ''}</Hug>
    </Hug>
  )
  const content = (
    <>
      <Hug h={40} flex={['aic', 'jcsb']}>
        <span>{length} incarnation{length !== 1 ? 's' : ''} selected</span>
        <Hug flex={['aic']}>
          <Link to="/incarnations/bulk-update" style={{ textDecoration: 'none' }}>
            <Button size="small" type="button">
              <Hug as="span" flex={['aic']}>
                Bulk update
                <Hug as="span" ml={4}>
                  <Bulk width={16} height={16} />
                </Hug>
              </Hug>
            </Button>
          </Link>
          <Hug ml={4}>
            <Button size="small" onClick={clearAll}>
              <Hug as="span" flex={['aic']}>
              Clear
                <Hug as="span" ml={4}>
                  <Close width={16} height={16} />
                </Hug>
              </Hug>
            </Button>
          </Hug>
        </Hug>
      </Hug>
      {showProgress && progressContent}
    </>
  )
  return (
    <Container>
      <Box show={show}>
        <Header>
          {content}
        </Header>
      </Box>
    </Container>
  )
}
