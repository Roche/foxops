import { useEventListener } from 'usehooks-ts'

export const useColResizeBodyCursor = () => {
  const onMousedown = (e: MouseEvent) => {
    if (e.target instanceof Element && e.target.closest('.resizer')) {
      document.body.style.cursor = 'col-resize'
    }
  }
  const onMouseup = () => {
    document.body.style.cursor = ''
  }
  useEventListener('mousedown', onMousedown)
  useEventListener('mouseup', onMouseup)
}
