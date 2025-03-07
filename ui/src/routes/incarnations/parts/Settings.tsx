import { useMemo, useState } from 'react'
import { Tooltip } from '../../../components/common/Tooltip/Tooltip'
import { IconButton } from '../../../components/common/IconButton/IconButton'
import { Settings as SettingsIcon } from '../../../components/common/Icons/Settings'
import { Popover } from '../../../components/common/Popover/Popover'
import { Hug } from '../../../components/common/Hug/Hug'
import { Checkbox } from '../../../components/common/Checkbox/Checkbox'
import { INCARNATION_TABLE_COLUMNS } from '../../../constants/incarnations.consts'
import { IncarnationBase } from '../../../interfaces/incarnations.types'
import { useTableSettingsStore } from '../../../stores/table-settings'
import { ToggleSwitch } from '../../../components/common/ToggleSwitch/ToggleSwitch'
import { Divider } from '../../../components/common/Divider/Divider'
import styled from '@emotion/styled'

const FIELDS = INCARNATION_TABLE_COLUMNS
  .map(
    x => ({ id: x.id, label: x.header })
  )

const MIN_VISIBLE_COLUMNS = 3

export const Settings = () => {
  const [settingsEl, setSettingsEl] = useState<HTMLButtonElement | null>(null)
  const [open, setOpen] = useState(false)

  const onClose = (e: MouseEvent | TouchEvent) => {
    if (!(e.target instanceof Element)) return
    if (e.target.closest('.Popover') || e.target.closest('.settings-button')) return
    setOpen(false)
  }
  const onSettingsClick = () => setOpen(x => !x)
  const {
    visibleColumns,
    setVisibleColumns,
    tableDensity,
    setDensity,
    withPagination,
    setWithPagination
  } = useTableSettingsStore()
  const visibleColumnsIds = useMemo(
    () => visibleColumns.map(x => x.id),
    [visibleColumns]
  )
  const handleChangeFieldsVisibility = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setVisibleColumns([...visibleColumnsIds, e.target.name as keyof IncarnationBase])
    } else {
      setVisibleColumns(visibleColumnsIds.filter(x => x !== e.target.name))
    }
  }

  const handleDensityChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setDensity(e.target.checked ? 'compact' : 'comfortable')
  }

  const handleSetWithPagination = (e: React.ChangeEvent<HTMLInputElement>) => {
    setWithPagination(e.target.checked)
  }
  return (
    <>
      <Tooltip title={open ? '' : 'Table settings'}>
        <div>
          <IconButton
            className="settings-button"
            ref={setSettingsEl}
            active={open}
            onClick={onSettingsClick}>
            <SettingsIcon />
          </IconButton>
        </div>
      </Tooltip>
      <Popover
        open={open}
        anchorEl={settingsEl}
        onClickOutside={onClose}>
        <Hug p={16}>
          <Hug mb={8} style={{ color: 'var(--grey-600)', fontSize: 20 }}>Visible Table Fields</Hug>
          <Hug maw={500} flex={['aic', 'fxww']} mb={8}>
            {FIELDS.map(x => (
              <Hug
                allw="50%"
                px={8}
                my={8}
                key={x.id}>
                <Checkbox
                  disabled={visibleColumns.length === MIN_VISIBLE_COLUMNS + 1 && visibleColumnsIds.includes(x.id)}
                  label={x.label}
                  name={x.id}
                  checked={visibleColumnsIds.includes(x.id as keyof IncarnationBase)}
                  onChange={handleChangeFieldsVisibility} />
              </Hug>
            ))}
          </Hug>
          <Hug mx={-24}><Divider /></Hug>
          <Hug ml={8} mt={16} flex={['fxdc']} gap={16}>
            <ToggleSwitch
              checked={tableDensity === 'compact'}
              label="Compact Density"
              size="small"
              onChange={handleDensityChange} />
            <ToggleSwitch
              checked={withPagination}
              label="Pagination"
              size="small"
              onChange={handleSetWithPagination} />
          </Hug>
          <Hug mt={24}>
            <Tip>💡 Tip: Hold Shift + Click on sorting icon will sort by multiple columns</Tip>
          </Hug>
        </Hug>
      </Popover>
    </>
  )
}

const Tip = styled.div`
  margin-left: 8px;
  color: var(--grey-500);
  font-size: 14px;
`
