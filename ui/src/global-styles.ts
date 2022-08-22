import { css, Theme } from '@emotion/react'
import normalize from 'normalize.css'

export const createGlobalStyles = ({
  colors: {
    baseBg,
    text,
    orange
  }
}: Theme) => css`
  ${normalize}
  :root {
    --base-easing: cubic-bezier(.66,.09,.85,.52);
    --ease-in: ease-in;
    --ease-out: ease-out;
    --monospace-font: 'Lucida Console', Monaco, Monospace;
    color: ${text};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
      "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji",
      "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
  }
  html {
    background-color: ${baseBg};
  }
  html, body {
    height: 100%;
  }
  #root {
    height: 100%;
    overflow: hidden;
  }
  * {
    box-sizing: border-box;
  }
  svg {
    vertical-align: middle;
  }
  a {
    color: ${orange}
  }
`
