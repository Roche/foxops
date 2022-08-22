import '@emotion/react'

declare module '@emotion/react' {
  export interface Theme {
    colors: {
      baseBg: string
      asideBg: string
      text: string
      textContrast: string
      asideBorder: string
      inputBorder: string,
      paleOrange: string,
      orange: string,
      iconButtonCurtain: string,
      iconButtonBorder: string,
      iconButtonColor: string,
      grey: string
    },
    effects: {
      orangeGradient: string
      toolbarDropShadow: string,
      popoverShadow: string
    },
    zIndex: {
      popover: number,
      toolbar: number,
      aside: number,
    }
  }
}
