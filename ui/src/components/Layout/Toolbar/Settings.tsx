import { useState } from 'react'
import { Tooltip } from '../../common/Tooltip/Tooltip'
import { IconButton } from '../../common/IconButton/IconButton'
import { Settings as SettingsIcon } from '../../common/Icons/Settings'
import { Popover } from '../../common/Popover/Popover'
import { Hug } from '../../common/Hug/Hug'
import { Checkbox } from '../../common/Checkbox/Checkbox'
import { INCARNATION_TABLE_COLUMNS } from '../../../constants/incarnations.consts'
import { IncarnationBase } from '../../../interfaces/incarnations.types'
import { useTableSettingsStore } from '../../../stores/table-settings'

const FIELDS = INCARNATION_TABLE_COLUMNS
  .filter(x => x.id !== 'id')
  .map(
    x => ({ id: x.id, label: x.header })
  )

export const Settings = () => {
  const [settingsEl, setSettingsEl] = useState<HTMLButtonElement | null>(null)
  const [open, setOpen] = useState(false)

  const onClose = (e: MouseEvent | TouchEvent) => {
    if (!(e.target instanceof Element)) return
    if (e.target.closest('.Popover') || e.target.closest('.settings-button')) return
    setOpen(false)
  }
  const onSettingsClick = () => setOpen(x => !x)
  const { visibleColumns, setVisibleColumns } = useTableSettingsStore()
  const handleChangeFieldsVisibility = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setVisibleColumns([...visibleColumns, e.target.name as keyof IncarnationBase])
    } else {
      setVisibleColumns(visibleColumns.filter(x => x !== e.target.name))
    }
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
        open={true}
        anchorEl={settingsEl}
        onClickOutside={onClose}>
        {/* 
        fields,
        table density,
        simple actions (increases performance slightly)
        */}
        <Hug p={16}>
          <Hug ml={32} mb={8} style={{ color: 'var(--grey-600)', fontSize: 20 }}>Visible Table Fields</Hug>
          <Hug maw={500} flex={['aic', 'fxww']}>
            {FIELDS.map(x => (
              <Hug
                allw="50%"
                px={8}
                my={8}
                key={x.id}>
                <Checkbox
                  disabled={visibleColumns.length === 5 && visibleColumns.includes(x.id)}
                  label={x.label}
                  name={x.id}
                  checked={visibleColumns.includes(x.id as keyof IncarnationBase)}
                  onChange={handleChangeFieldsVisibility} />
              </Hug>
            ))}
          </Hug>
          {/* <Hug ml={32} mb={8} style={{ color: 'var(--grey-600)', fontSize: 20 }}>Density</Hug> */}
          
        </Hug>
      </Popover>
    </>
  )
}
