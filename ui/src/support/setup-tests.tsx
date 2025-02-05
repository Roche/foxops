import '@testing-library/jest-dom'
import React, { ReactElement, act } from 'react'
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
export { act }
export { customRender as render }
