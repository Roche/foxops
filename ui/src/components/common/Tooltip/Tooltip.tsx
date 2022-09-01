import { useState, Children, cloneElement, CSSProperties } from 'react'
import { useFloating, offset, flip, shift, useInteractions, useHover, Placement, safePolygon, FloatingPortal } from '@floating-ui/react-dom-interactions'
import styled from '@emotion/styled'
import { motion, AnimatePresence } from 'framer-motion'

const TooltipBody = styled(motion.div)(({ theme }) => ({
  zIndex: theme.zIndex.tooltip
}))

const TooltipContent = styled.div(({ theme }) => ({
  background: theme.colors.tooltipBg,
  maxWidth: 300,
  fontSize: 11,
  padding: '4px 8px',
  borderRadius: 4,
  color: theme.colors.textContrast,
  whiteSpace: 'normal',
  wordWrap: 'break-word'
}))

interface TooltipProps {
  children: React.ReactElement,
  title: React.ReactNode,
  dataTestid?: string,
  placement?: Placement,
  style?: CSSProperties
}

export const Tooltip = ({ children, title, dataTestid, placement = 'bottom', style }: TooltipProps) => {
  const [open, setOpen] = useState(false)
  const { x, y, reference, floating, strategy, context } = useFloating({
    middleware: [offset(8), flip(), shift()],
    open,
    onOpenChange: setOpen,
    placement
  })
  const { getReferenceProps, getFloatingProps } = useInteractions([useHover(context, { restMs: 400, handleClose: safePolygon() })])
  try {
    Children.only(children)
  } catch (error) {
    console.error(error)
    return children
  }
  const element = cloneElement(children, {
    ...children.props,
    ...getReferenceProps(),
    ref: reference
  })
  return (
    <>
      {element}
      <FloatingPortal>
        <AnimatePresence>
          {open && (
            <TooltipBody
              data-testid={dataTestid}
              initial={{ opacity: 0, scale: 0.85 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              transition={{ type: 'spring', damping: 20, stiffness: 300 }}
              ref={floating}
              style={{
                position: strategy,
                top: y ?? 0,
                left: x ?? 0,
                ...style
              }}
              {...getFloatingProps()}>
              <TooltipContent>{title}</TooltipContent>
            </TooltipBody>
          )}
        </AnimatePresence>
      </FloatingPortal>
    </>
  )
}
