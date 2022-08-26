import { css, Theme } from '@emotion/react'
import normalize from 'normalize.css'
// import prism from './styling/prism.css' TODO: include it when JSON editor is ready

export const createGlobalStyles = ({
  colors
}: Theme) => css`
  ${normalize}
  :root {
    --base-easing: cubic-bezier(.66,.09,.85,.52);
    --ease-in: ease-in;
    --ease-out: ease-out;
    --monospace: 'Lucida Console', Monaco, Monospace;
    color: ${colors.text};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
      "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji",
      "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
  }
  html {
    background-color: ${colors.baseBg};
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
    color: ${colors.text}
  }
  a:hover {
    text-decoration: none;
  }
  
  @keyframes toolbar-progress {
    0% {
      transform: scaleX(0);
    }
    10% {
      transform: scaleX(.25);
    }
    25% {
      transform: scaleX(.25);
    }
    50% {
      transform: scaleX(.45);
    }
    66% {
      transform: scale(.7);
    }
    88% {
      transform: scale(.7);
    }
    100% {
      transform: scale(.9);
    }
  }
  @keyframes toolbar-progress-done {
    to {
      transform: scaleX(1);
      opacity: 0;
    }
  }
`
