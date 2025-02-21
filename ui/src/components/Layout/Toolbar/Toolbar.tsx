import styled from '@emotion/styled'
import { useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../../../stores/auth'
import { useThemeModeStore } from '../../../stores/theme-mode'
import { Button, ButtonLink } from '../../common/Button/Button'
import { Hug } from '../../common/Hug/Hug'
import { IconButton } from '../../common/IconButton/IconButton'
import { DarkMode } from '../../common/Icons/DarkMode'
import { LightMode } from '../../common/Icons/LightMode'
import { User } from '../../common/Icons/User'
import { Logo } from '../../common/Logo/Logo'
import { Popover } from '../../common/Popover/Popover'
import { ToolbarProgress } from '../../common/ToolbarProgress/ToolbarProgress'
import { Tooltip } from '../../common/Tooltip/Tooltip'

const Box = styled.div`
  box-shadow: ${p => p.theme.effects.toolbarDropShadow};
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-left: 8px;
  padding-right: 8px;
  z-index: ${p => p.theme.zIndex.toolbar};
  background: ${p => p.theme.colors.baseBg};
`

export const Toolbar = () => {
  const [profileOpen, setProfileOpen] = useState(false)
  const { mode, toggleMode } = useThemeModeStore()
  const { setToken } = useAuthStore()
  const [profileIconEl, setProfileIconEl] = useState<HTMLButtonElement | null>(null)

  const onProfileClick = () => setProfileOpen(x => !x)
  const onClose = (e: MouseEvent | TouchEvent) => {
    if (!(e.target instanceof Element)) return
    if (e.target.closest('.Popover') || e.target.closest('.profile-button')) return
    setProfileOpen(false)
  }
  const queryClient = useQueryClient()
  const onLogout = () => {
    setToken(null)
    queryClient.removeQueries(['incarnations'])
  }
  return (
    <Box className="Toolbar-Box" data-testid="Toolbar">
      <ToolbarProgress />
      <Link to="/incarnations" style={{ color: 'inherit', textDecoration: 'none' }}><Logo /></Link>
      <Hug ml={16} mr="auto">
        <ButtonLink
          dataTestid="create-incarnation-button"
          to="/incarnations/create"
          outline>+ Create Incarnation</ButtonLink>
      </Hug>
      <Hug flex className="Toolbar-Controls" data-testid="Toolbar-Controls">
        <Hug mr={8}>
          <Tooltip title={`Toggle ${mode} mode`}>
            <IconButton onMouseDown={e => e.preventDefault()} onClick={toggleMode}>
              {mode === 'dark' ? <LightMode /> : <DarkMode />}
            </IconButton>
          </Tooltip>
        </Hug>
        <IconButton
          className="profile-button"
          ref={setProfileIconEl}
          active={profileOpen}
          onClick={onProfileClick}>
          <User />
        </IconButton>
        <Popover open={profileOpen} anchorEl={profileIconEl} onClickOutside={onClose}>
          <Button onClick={onLogout}>Logout</Button>
        </Popover>
      </Hug>
    </Box>
  )
}
