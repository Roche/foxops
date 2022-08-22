import '@testing-library/jest-dom/extend-expect'
import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { ThemeProvider } from '@emotion/react'
import { THEMES } from '../styling/themes'

const AllTheProviders = ({ children }: { children: React.ReactNode }) => (
  <ThemeProvider theme={THEMES.light}>{children}</ThemeProvider>
)

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

export * from '@testing-library/react'
export { customRender as render }
