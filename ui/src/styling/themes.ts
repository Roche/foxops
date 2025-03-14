import { Theme } from '@emotion/react'
import { ThemeMode } from '../shared/types'

const zIndex = {
  popover: 12,
  toolbar: 11,
  aside: 5, // should be less than toolbar
  floatingActionButton: 5,
  tooltip: 12
}

const sizes = {
  toolbar: 60,
  aside: 57
}
const greyPalette = {
  50: '#FAF9F7',
  100: '#E8E6E1',
  200: '#D3CEC4',
  300: '#B8B2A7',
  400: '#A39E93',
  500: '#857F72',
  600: '#625D52',
  700: '#504A40',
  800: '#423D33',
  900: '#27241D'
}

export const THEMES: Record<ThemeMode, Theme> = {
  light: {
    mode: 'light',
    colors: {
      baseBg: '#fff',
      asideBg: '#F5F5F5',
      text: '#333',
      contrastText: '#fff',
      asideBorder: '#D2D2D2',
      inputBorder: '#d2d2d2',
      paleOrange: '#fcbf49',
      orange: '#EA6E00',
      iconButtonCurtain: '#d2d2d2',
      iconButtonBorder: '#d2d2d2',
      iconButtonColor: '#363636',
      grey: '#d2d2d2',
      darkGrey: '#929292',
      error: '#de4242',
      tooltipBg: '#333',
      statusSuccess: '#EA6E00',
      statusFailure: '#de4242',
      statusPending: '#6f5811',
      statusUnknown: '#333'
    },
    effects: {
      orangeGradient: 'linear-gradient(130deg, #EA6E00, #FFAC63)',
      toolbarDropShadow: '0px 2px 4px rgba(0, 0, 0, 0.25)',
      popoverShadow: '0px 2px 4px rgba(0, 0, 0, 0.25)',
      actionButtonShadow: '0px 3px 5px -1px rgb(0 0 0 / 20%), 0px 6px 10px 0px rgb(0 0 0 / 14%), 0px 1px 18px 0px rgb(0 0 0 / 12%)',
      actionButtonHoverShadow: '0px 7px 8px -4px rgb(0 0 0 / 20%), 0px 12px 17px 2px rgb(0 0 0 / 14%), 0px 5px 22px 4px rgb(0 0 0 / 12%)',
      incarnationOperationWindowShadow: '0px 0px 4px 0 rgba(0, 0, 0, 0.25)',
      paperShadow: '0px 2px 4px rgba(0, 0, 0, 0.25)'
    },
    zIndex,
    sizes,
    palettes: {
      grey: greyPalette
    }
  },
  dark: {
    mode: 'dark',
    colors: {
      baseBg: '#333',
      asideBg: '#444444',
      text: '#fff',
      contrastText: '#fff',
      asideBorder: '#4e4e4e',
      inputBorder: '#d2d2d2',
      paleOrange: '#fcbf49',
      orange: '#EA6E00',
      iconButtonCurtain: '#4e4e4e',
      iconButtonBorder: '#cfcfcf',
      iconButtonColor: '#fff',
      grey: '#d2d2d2',
      darkGrey: '#929292',
      error: '#b62525',
      tooltipBg: '#555',
      statusSuccess: '#EA6E00',
      statusFailure: '#de4242',
      statusPending: '#c6980b',
      statusUnknown: '#fff'
    },
    effects: {
      orangeGradient: 'linear-gradient(130deg, #EA6E00, #ae5718)',
      toolbarDropShadow: '0px 2px 4px rgba(0, 0, 0, 0.25)',
      popoverShadow: '0px 2px 4px rgba(0, 0, 0, 0.25)',
      actionButtonShadow: '0px 3px 5px -1px rgb(0 0 0 / 20%), 0px 6px 10px 0px rgb(0 0 0 / 14%), 0px 1px 18px 0px rgb(0 0 0 / 12%)',
      actionButtonHoverShadow: '0px 7px 8px -4px rgb(0 0 0 / 20%), 0px 12px 17px 2px rgb(0 0 0 / 14%), 0px 5px 22px 4px rgb(0 0 0 / 12%)',
      incarnationOperationWindowShadow: '0px 0px 4px 0 rgba(0, 0, 0, 0.25)',
      paperShadow: '0px 2px 4px rgba(0, 0, 0, 0.25)'
    },
    zIndex,
    sizes,
    palettes: {
      grey: greyPalette
    }
  }
}
