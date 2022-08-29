interface Translate {
  x?: number,
  y?: number
}
interface Transform {
  scale?: number,
  translate?: number | string | Translate
}
export const buildTransform = ({ translate, scale }: Transform = {}) => {
  const transform = []
  if (translate) {
    if (typeof translate === 'string') {
      transform.push(`translate(${translate})`)
    } else if (typeof translate === 'number') {
      transform.push(`translate(${translate}px)`)
    } else {
      transform.push(`translate(${translate.x ?? 0}px, ${translate.y ?? 0}px)`)
    }
  }
  if (scale) {
    transform.push(`scale(${scale})`)
  }
  return transform.length ? transform.join(' ') : 'none'
}
