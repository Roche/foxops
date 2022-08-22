import { useEffect } from 'react'

export function useOnClickOutside(ref: { current: null | HTMLElement }, handler: (event: MouseEvent | TouchEvent) => void) {
  useEffect(
    () => {
      const listener = (event: MouseEvent | TouchEvent) => {
        // Do nothing if clicking ref's element or descendent elements
        if (!(event.target instanceof Element)) return
        if (!ref.current || ref.current.contains(event.target)) {
          return
        }
        handler(event)
      }
      // Mousedown and touchstart is chosen because it's fired before click
      // if the hook is used for popovers, then clicking on other button for the same popover
      // will close it before this click finishes
      document.addEventListener('mousedown', listener)
      document.addEventListener('touchstart', listener)
      return () => {
        document.removeEventListener('mousedown', listener)
        document.removeEventListener('touchstart', listener)
      }
    },
    // Add ref and handler to effect dependencies
    // It's worth noting that because passed in handler is a new ...
    // ... function on every render that will cause this effect ...
    // ... callback/cleanup to run every render. It's not a big deal ...
    // ... but to optimize you can wrap handler in useCallback before ...
    // ... passing it into this hook.
    [ref, handler]
  )
}
