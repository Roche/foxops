import { css, Theme } from '@emotion/react'
import normalize from 'normalize.css?inline'
import { ThemeMode } from './shared/types'
// import prism from './styling/prism.css' TODO: include it when JSON editor is ready

export const createGlobalStyles = ({ colors }: Theme, mode: ThemeMode) => css`
  ${normalize}
  :root {
    ${mode === 'dark'
    ? `
      --d2h-dark-bg-color:rgba(12, 17, 23, 0.47);
      --d2h-moved-label-color: rgb(12, 130, 249);`
    : ` 
      --d2h-dark-bg-color: #f1f1f1;
      --d2h-bg-color: #f7f7f7;`}
    --grey-50: #F7F7F7;
    --grey-100: #e1e1e1;
    --grey-200: #cfcfcf;
    --grey-300: #b1b1b1;
    --grey-400: #9e9e9e;
    --grey-500: #7e7e7e;
    --grey-600: #626262;
    --grey-700: #515151;
    --grey-800: #3b3b3b;
    --grey-900: #222222;
    --orange-500: #ea6e00;
    --base-easing: cubic-bezier(0.66, 0.09, 0.85, 0.52);
    --ease-in: ease-in;
    --ease-out: ease-out;
    --monospace: "Lucida Console", Monaco, Monospace;
    --base-bg: ${colors.baseBg};
    --primary: var(--orange-500);
    color: ${colors.text};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
      "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji",
      "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";

    --actions-column-shadow: -4px 0 4px 0
      var(${mode === 'dark' ? '--grey-900' : '--grey-100'});
  }
  html {
    background-color: ${colors.baseBg};
  }
  html,
  body {
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
    color: ${colors.text};
  }
  a:hover {
    text-decoration: none;
  }

  .diff-file-link {
    cursor: pointer;
    text-decoration: underline;
  }

  .d2h-file-name {
    user-select: none;
  }

  .d2h-file-wrapper {
    background-color: var(--d2h-dark-bg-color);
  }

  .d2h-wrapper {
    background-color: transparent;
  }

  @keyframes toolbar-progress {
    0% {
      transform: scaleX(0);
    }
    10% {
      transform: scaleX(0.25);
    }
    25% {
      transform: scaleX(0.25);
    }
    50% {
      transform: scaleX(0.45);
    }
    66% {
      transform: scale(0.7);
    }
    88% {
      transform: scale(0.7);
    }
    100% {
      transform: scale(0.9);
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
  @keyframes bounce {
    0%,
    20%,
    50%,
    80%,
    100% {
      transform: scale(1);
    }
    40% {
      transform: scale(1.08);
    }
    60% {
      transform: scale(1.04);
    }
  }

  @keyframes loadbar {
    0% {
      width: 0;
    }
    100% {
      width: 100%;
    }
  }

  @keyframes error-close {
    0% {  
      transform: rotateX(0deg);
      opacity: 1;
    }
    100% {
      transform: rotateX(90deg);
      opacity: 0;
    }
  }
`
