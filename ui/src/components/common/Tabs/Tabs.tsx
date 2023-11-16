import styled from '@emotion/styled'
import { useState } from 'react'

export interface TabsProps {
  defaultTab?: number
  tabs: {
    label: React.ReactNode
    content: React.ReactNode
  }[]
}

export const Tabs = ({
  defaultTab = 0,
  tabs
}: TabsProps) => {
  const [activeTab, setActiveTab] = useState(defaultTab)
  const active = tabs[activeTab]
  return (
    <TabsBox>
      <TabsNav>
        {tabs.map((tab, i) => (
          <TabsNavItem
            key={i}
            active={i === activeTab}
            onClick={() => setActiveTab(i)}
          >{tab.label}</TabsNavItem>
        ))}
      </TabsNav>
      <TabsBody>
        {active.content}
      </TabsBody>
    </TabsBox>
  )
}

const TabsBox = styled.div`
  display: flex;
  flex-direction: column;
  overflow: hidden;
`

const TabsNav = styled.ul`
  display: flex;
  flex-direction: row;
  list-style: none;
  padding: 0;
  margin: 0;
`

const TabsNavItem = styled.li<{active: boolean}>`
  flex: 1 0 auto;
  border-bottom: 2px solid ${({ theme, active }) => active ? theme.colors.orange : theme.colors.grey};
  padding: 12px 16px;
  cursor: pointer;
  background-color: ${({ theme, active }) => active ? (theme.mode === 'light' ? theme.palettes.grey[50] : theme.palettes.grey[900]) : theme.colors.baseBg};
  &:hover {
    background-color: ${({ theme }) => theme.mode === 'light' ? theme.palettes.grey[50] : theme.palettes.grey[900]};
  }
`

const TabsBody = styled.div`
`
