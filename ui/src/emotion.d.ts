import '@emotion/react'

interface Palette {
  50: string
  100: string
  200: string
  300: string
  400: string
  500: string
  600: string
  700: string
  800: string
  900: string
}

declare module '@emotion/react' {
  export interface Theme {
    mode: 'light' | 'dark'
    colors: {
      baseBg: string
      asideBg: string
      text: string
      contrastText: string
      asideBorder: string
      inputBorder: string,
      paleOrange: string,
      orange: string,
      iconButtonCurtain: string,
      iconButtonBorder: string,
      iconButtonColor: string,
      grey: string,
      darkGrey: string,
      error: string,
      tooltipBg: string,
      statusSuccess: string,
      statusFailure: string,
      statusPending: string,
      statusUnknown: string
    },
    palettes: {
      grey: Palette
    }
    effects: {
      orangeGradient: string
      toolbarDropShadow: string,
      popoverShadow: string,
      actionButtonShadow: string,
      actionButtonHoverShadow: string,
      incarnationOperationWindowShadow: string,
      paperShadow: string
    },
    zIndex: {
      popover: number,
      toolbar: number,
      aside: number,
      floatingActionButton: number,
      tooltip: number
    },
    sizes: {
      toolbar: number,
      aside: number
    }
  }
}
