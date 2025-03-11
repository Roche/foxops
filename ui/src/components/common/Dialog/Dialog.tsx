import { useState } from 'react'
import styled from '@emotion/styled'

const DialogOverlay = styled.div`
  width: 100vw;
  height: 100vh;
  position: fixed;
  top: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100000;
  background: rgba(0, 0, 0, 0.4);
`

const DialogContent = styled.div(({ theme }) => ({
  background: theme.colors.baseBg,
  borderRadius: 8,
  padding: 16,
  boxShadow: theme.effects.popoverShadow,
  minWidth: 'min(80vw, 45rem)',
  minHeight: 'min(80vh, 20rem)',
  position: 'relative',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'start',
  alignItems: 'center'
}))

const DialogTitle = styled.h2(() => ({
  fontSize: 24,
  fontWeight: 600,
  marginBottom: 16,
  width: '100%',
  margin: 0,
  paddingLeft: '1rem',
  paddingTop: '1rem',
  height: '4rem'
}))

const DialogText = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: start;
  width: 100%;
  min-height: min(calc(80vh - 10rem), 10rem);
  padding: 1rem;
`

const DialogActions = styled.div`
  display: flex;
  justify-content: flex-end;
  width: 100%;
  padding: 0.8rem;
  height: 4rem;
`

const BaseButton = {
  borderRadius: 4,
  border: 'none',
  cursor: 'pointer',
  marginLeft: '.5rem',
  marginRight: '.5rem',
  minWidth: '6rem'
}

const AbortButton = styled.button(({ theme }) => ({
  ...BaseButton,
  background: theme.colors.orange,
  color: '#fff'
}))

const ConfirmButton = styled.button(({ theme }) => ({
  ...BaseButton,
  background: theme.colors.baseBg,
  color: theme.colors.text,
  borderWidth: 1,
  borderColor: theme.colors.orange,
  borderStyle: 'solid'
}))

type DialogProps = {
  children: React.ReactNode;
  title: string;
  open?: boolean;
  onConfirm?: () => void;
  onAbort?: () => void;
};

export const Dialog = ({ children, open, onConfirm, onAbort, title }: DialogProps) => {
  const [animateDialog, setAnimateDialog] = useState(false)

  return (
    <>
      {open && (
        <DialogOverlay onClick={() => setAnimateDialog(true)}>
          <DialogContent onAnimationEnd={() => setAnimateDialog(false)} style={{ animation: animateDialog ? 'bounce 0.3s' : '' }} onClick={e => e.stopPropagation()}>
            <DialogTitle>{title}</DialogTitle>
            <DialogText>{children}</DialogText>
            <DialogActions>
              <AbortButton onClick={() => onAbort && onAbort()}>Abort</AbortButton>
              <ConfirmButton onClick={() => onConfirm && onConfirm()}>
                Confirm
              </ConfirmButton>
            </DialogActions>
          </DialogContent>
        </DialogOverlay>
      )}
    </>
  )
}
