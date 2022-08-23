import styled from '@emotion/styled'
import { useState } from 'react'
import { useAuthStore } from '../../../stores/auth'
import { useThemeModeStore } from '../../../stores/theme-mode'
import { useToolbarSearchStore } from '../../../stores/toolbar-search'
import { Button } from '../../common/Button/Button'
import { Hug } from '../../common/Hug/Hug'
import { IconButton } from '../../common/IconButton/IconButton'
import { DarkMode } from '../../common/Icons/DarkMode'
import { LightMode } from '../../common/Icons/LightMode'
import { User } from '../../common/Icons/User'
import { Logo } from '../../common/Logo/Logo'
import { Popover } from '../../common/Popover/Popover'
import { TextField } from '../../common/TextField/TextField'

const Box = styled.div`
  grid-row: 1;
  grid-column: 1 / 3;
  box-shadow: ${p => p.theme.effects.toolbarDropShadow};
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-left: 8px;
  padding-right: 8px;
  position: relative;
  z-index: ${p => p.theme.zIndex.toolbar};
`

export const Toolbar = () => {
  const [profileOpen, setProfileOpen] = useState(false)
  const { mode, toggleMode } = useThemeModeStore()
  const { setToken } = useAuthStore()
  const [profileIconEl, setProfileIconEl] = useState<HTMLButtonElement | null>(null)
  const onProfileClick = () => setProfileOpen(x => !x)
  const onClose = (e: MouseEvent | TouchEvent) => {
    if (!(e.target instanceof Element)) return
    if (e.target.closest('.Popover') || e.target.closest('.Toolbar-IconButton--Profile')) return
    setProfileOpen(false)
  }
  const { search, setSearch } = useToolbarSearchStore()
  return (
    <Box className="Toolbar-Box" data-testid="Toolbar">
      <Logo />
      <Hug flex className="Toolbar-Controls" data-testid="Toolbar-Controls">
        <Hug mr={8}>
          <TextField placeholder="Search..." type="search" value={search} onChange={e => setSearch(e.target.value)} />
        </Hug>
        <Hug mr={8}>
          <IconButton className="Toolbar-IconButton" onMouseDown={e => e.preventDefault()} onClick={toggleMode}>
            {mode === 'dark' ? <LightMode /> : <DarkMode />}
          </IconButton>
        </Hug>
        <IconButton className="Toolbar-IconButton Toolbar-IconButton--Profile" ref={setProfileIconEl} active={profileOpen} onClick={onProfileClick}>
          <User />
        </IconButton>
      </Hug>
      <Popover open={profileOpen} anchorEl={profileIconEl} onClickOutside={onClose}>
        <Button onClick={() => setToken(null)}>Logout</Button>
      </Popover>
    </Box>
  )
}
