import { css, Theme } from '@emotion/react'
import normalize from 'normalize.css'
import { ThemeMode } from './shared/types'
// import prism from './styling/prism.css' TODO: include it when JSON editor is ready

export const createGlobalStyles = ({
  colors
}: Theme, mode: ThemeMode) => css`
  ${normalize}
  :root {
    --grey-50: #F7F7F7;
    --grey-100: #E1E1E1;
    --grey-200: #CFCFCF;
    --grey-300: #B1B1B1;
    --grey-400: #9E9E9E;
    --grey-500: #7E7E7E;
    --grey-600: #626262;
    --grey-700: #515151;
    --grey-800: #3B3B3B;
    --grey-900: #222222;
    --orange-500: #EA6E00;
    --base-easing: cubic-bezier(.66,.09,.85,.52);
    --ease-in: ease-in;
    --ease-out: ease-out;
    --monospace: 'Lucida Console', Monaco, Monospace;
    --base-bg: ${colors.baseBg};
    --primary: var(--orange-500);
    color: ${colors.text};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
      "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji",
      "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";

    --actions-column-shadow: -4px 0 4px 0 var(${mode === 'dark' ? '--grey-900' : '--grey-100'});
    
  }
  html {
    background-color: ${colors.baseBg};
  }
  html, body {
    height: 100%;
  }
  #root {
    min-height: 100%;
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
  @keyframes rotation {
    0% {
        transform: rotate(0deg);
    }
    100% {
        transform: rotate(360deg);
    }
  }
`
