import { Component } from 'react'
import { createPortal } from 'react-dom'

export const portalFactory = () => class Portal extends Component<{children: React.ReactNode}> {
  el = document.createElement('div')

  componentDidMount() {
    document.body.appendChild(this.el)
  }

  componentWillUnmount() {
    document.body.removeChild(this.el)
  }

  render() {
    return createPortal(
      this.props.children,
      this.el
    )
  }
}

