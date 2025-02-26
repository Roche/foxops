import styled from '@emotion/styled'
import { useEffect, useRef, useState } from 'react'
import { useOnClickOutside } from '../../../hooks/use-on-click-outside'
import { Hug } from '../Hug/Hug'
import { portalFactory } from '../Portal/Portal'

const PopoverPortal = portalFactory()

type PopoverBoxProps = {
  right: number,
  top: number
}

const Box = styled('div')<PopoverBoxProps>(({ theme, right, top }) => ({
  position: 'absolute',
  zIndex: theme.zIndex.popover,
  boxShadow: theme.effects.popoverShadow,
  right,
  top,
  background: theme.colors.baseBg,
  transform: 'translateY(4px)',
  borderRadius: 8
}))

interface PopoverProps {
  children: React.ReactNode,
  anchorEl: null | HTMLElement,
  open: boolean,
  onClickOutside: (e: MouseEvent | TouchEvent) => void
}

export const Popover = ({ children, anchorEl, open, onClickOutside }: PopoverProps) => {
  const [top, setTop] = useState(0)
  const [right, setRight] = useState(0)
  const popoverRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!anchorEl) return
    const rect = anchorEl.getBoundingClientRect()
    setRight(window.innerWidth - rect.right)
    setTop(rect.top + rect.height)
  }, [anchorEl])
  useOnClickOutside(popoverRef, onClickOutside)
  return open ? (
    <PopoverPortal>
      <Box right={right} top={top} ref={popoverRef} className="Popover-Box">
        <Hug p={8}>
          {children}
        </Hug>
      </Box>
    </PopoverPortal>
  ) : null
}
