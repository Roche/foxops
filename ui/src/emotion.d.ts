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
      grey: string,
      darkGrey: string,
      error: string,
      tooltipBg: string
    },
    effects: {
      orangeGradient: string
      toolbarDropShadow: string,
      popoverShadow: string,
      actionButtonShadow: string,
      actionButtonHoverShadow: string
    },
    zIndex: {
      popover: number,
      toolbar: number,
      aside: number,
      floatingActionButton: number
    }
  }
}
