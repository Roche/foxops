import { css } from '@emotion/react'
import normalize from 'normalize.css'

const globalStyles = css`
  ${normalize}
  :root {
    --base-bg: rgb(240, 240, 240);
    --black: #333333;
    --pale-grey: #e0e0e0;
    --grey: #d2d2d2;
    --dark-grey: #8a8a8a;
    --pale-orange: #fcbf49;
    --orange: #ee6e00;
    --easing: cubic-bezier(.66,.09,.85,.52);
    --monospace-font: 'Lucida Console', Monaco, Monospace;
    background-color: var(--base-bg);
    color: var(--black);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
      "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji",
      "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
  }
  html, body {
    height: 100%;
  }
  #root {
    min-height: 100%;
    overflow: hidden;
  }
  * {
    box-sizing: border-box;
  }
`

export default globalStyles
