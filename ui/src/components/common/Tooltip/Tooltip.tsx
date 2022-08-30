import React, { useState } from 'react'
import { useFloating, offset, flip, shift, useInteractions, useHover } from '@floating-ui/react-dom-interactions'
import styled from '@emotion/styled'
import { motion, AnimatePresence } from 'framer-motion'

const TooltipBody = styled(motion.div)(({ theme }) => ({
  background: theme.colors.tooltipBg,
  fontSize: 12,
  padding: 8,
  borderRadius: 4,
  color: theme.colors.textContrast,
  maxWidth: 300,
  whiteSpace: 'normal'
}))

interface TooltipProps {
  children: React.ReactElement,
  title: React.ReactNode
}

export const Tooltip = ({ children, title }: TooltipProps) => {
  const [open, setOpen] = useState(false)
  const { x, y, reference, floating, strategy, context } = useFloating({
    middleware: [offset(8), flip(), shift()],
    open,
    onOpenChange: setOpen
  })
  const { getReferenceProps, getFloatingProps } = useInteractions([useHover(context, { restMs: 400 })])
  try {
    React.Children.only(children)
  } catch (error) {
    console.error(error)
    return children
  }
  const element = React.cloneElement(children, {
    ...children.props,
    ...getReferenceProps(),
    ref: reference
  })
  return (
    <>
      {element}
      <AnimatePresence>
        {!!title && open && (
          <TooltipBody
            initial={{ opacity: 0, scale: 0.85 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ type: 'spring', damping: 20, stiffness: 300 }}
            ref={floating}
            style={{
              position: strategy,
              top: y ?? 0,
              left: x ?? 0
            }}
            {...getFloatingProps()}>
            {title}
          </TooltipBody>
        )}
      </AnimatePresence>
    </>
  )
}
