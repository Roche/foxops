import { render, screen, fireEvent, act } from '../../../support/setup-tests'
import { delay } from '../../../utils'
import { Tooltip } from './Tooltip'

test('Tooltip should be displayed on hover', async () => {
  act(() => {
    render(
      <Tooltip dataTestid="Tooltip-Content" title="Tooltip content">
        <div data-testid="Tooltip-Anchor">Tooltip anchor</div>
      </Tooltip>
    )
  })
  const anchor = screen.getByTestId('Tooltip-Anchor')
  expect(anchor).toHaveTextContent('Tooltip anchor')
  await act(async () => {
    fireEvent.mouseMove(anchor)
    await delay(400) // need a little time to show the tooltip, because of the animation
  })
  const tooltip = screen.getByTestId('Tooltip-Content')
  expect(tooltip).toHaveTextContent('Tooltip content')
})
