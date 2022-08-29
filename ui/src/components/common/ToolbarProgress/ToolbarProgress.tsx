import styled from '@emotion/styled'
import { useRequestProcessingStore } from '../../../stores/request-processing-store'

const Box = styled.div`
  position: absolute;
  bottom: -1px;
  height: 1px;
  width: 100%;
  left: 0;
`

interface LineProps {
  done: boolean
}

const Line = styled.div<LineProps>`
  position: absolute;
  background-color: ${p => p.theme.colors.orange};
  width: 100%;
  height: 2px;
  left: 0;
  top: 0;
  box-shadow: 0 0 4px 0 ${p => p.theme.colors.orange};
  transform-origin: 0 50%;
  animation: ${p => p.done ? 'toolbar-progress-done 500ms ease-in-out both' : 'toolbar-progress 10s ease-in-out both'};
`

export const ToolbarProgress = () => {
  const { pending } = useRequestProcessingStore()
  return (
    <Box>
      <Line done={!pending} />
    </Box>
  )
}
