import { keyframes } from '@emotion/react'
import styled from '@emotion/styled'

const emojiKeyframes = keyframes`
  0% {
    content: "🕛";
  }
  8.3333333333% {
    content: "🕐";
  }
  16.6666666667% {
    content: "🕑";
  }
  25% {
    content: "🕒";
  }
  33.3333333333% {
    content: "🕓";
  }
  41.6666666667% {
    content: "🕔";
  }
  50% {
    content: "🕕";
  }
  58.3333333333% {
    content: "🕖";
  }
  66.6666666667% {
    content: "🕗";
  }
  75% {
    content: "🕘";
  }
  83.3333333333% {
    content: "🕙";
  }
  91.6666666667% {
    content: "🕚";
  }
`

export const Loader = styled.div`
  width: 1em;
  height: 1em;
  &::before {
    content: "🕛";
    animation: ${emojiKeyframes} steps(12) 1s infinite;
  }
`
