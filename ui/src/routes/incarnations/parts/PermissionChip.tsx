import { Eye } from 'components/common/Icons/Eye'
import { Group } from 'components/common/Icons/Group'
import { Pen } from 'components/common/Icons/Pen'
import styled from '@emotion/styled'
import { Hug } from 'components/common/Hug/Hug'
import { User } from 'components/common/Icons/User'

export interface UserChipProps {
    type: 'user' | 'group'
    name: string
    permission: 'read' | 'write'
}

const Chip = styled.div(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  color: theme.colors.text,
  borderRadius: '2rem',
  padding: '0.5rem',
  width: 'fit-content',
  border: `1px solid ${theme.colors.text}`,
  margin: '0.5rem',
  marginLeft: 0
}))

const Name = styled.span(({ theme }) => ({
  color: theme.colors.text,
  fontWeight: 500,
  marginRight: '0.5rem',
  userSelect: 'none'
}))

export const PermissionChip = ({ type, name, permission }: UserChipProps) => (
  <Chip>
    <Hug mr={4}>
      {
        type === 'user'
          ? <User height={16}></User>
          : <Group height={16}></Group>
      }
    </Hug>
    <Name>{name}</Name>
    {
      permission === 'write'
        ? <Pen height={16}></Pen>
        : <Eye height={16}></Eye>
    }
  </Chip>
)
