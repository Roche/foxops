import { Theme } from '@emotion/react'
import { ThemeMode } from '../shared/types'

const zIndex = {
  popover: 10,
  toolbar: 7,
  aside: 4 // should be less than toolbar
}

export const THEMES: Record<ThemeMode, Theme> = {
  light: {
    colors: {
      baseBg: '#fff',
      asideBg: '#F5F5F5',
      text: '#333',
      textContrast: '#fff',
      asideBorder: '#D2D2D2',
      inputBorder: '#d2d2d2',
      paleOrange: '#fcbf49',
      orange: '#EA6E00',
      iconButtonCurtain: '#d2d2d2',
      iconButtonBorder: '#d2d2d2',
      iconButtonColor: '#363636',
      grey: '#d2d2d2',
      darkGrey: '#929292'
    },
    effects: {
      orangeGradient: 'linear-gradient(130deg, #EA6E00, #FFAC63)',
      toolbarDropShadow: '0px 2px 4px rgba(0, 0, 0, 0.25)',
      popoverShadow: '0px 2px 4px rgba(0, 0, 0, 0.25)'
    },
    zIndex
  },
  dark: {
    colors: {
      baseBg: '#333',
      asideBg: '#444',
      text: '#fff',
      textContrast: '#fff',
      asideBorder: '#4e4e4e',
      inputBorder: '#d2d2d2',
      paleOrange: '#fcbf49',
      orange: '#EA6E00',
      iconButtonCurtain: '#4e4e4e',
      iconButtonBorder: '#cfcfcf',
      iconButtonColor: '#fff',
      grey: '#d2d2d2',
      darkGrey: '#929292'
    },
    effects: {
      orangeGradient: 'linear-gradient(130deg, #EA6E00, #ae5718)',
      toolbarDropShadow: '0px 2px 4px rgba(0, 0, 0, 0.25)',
      popoverShadow: '0px 2px 4px rgba(0, 0, 0, 0.25)'
    },
    zIndex
  }
}