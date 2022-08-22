export const transparentize = (hex: string, alpha: number) => {
  if (hex.charAt(0) !== '#' || hex.length < 4 || hex.length > 7) {
    throw new Error('Invalid hex color')
  }
  if (alpha < 0 || alpha > 1) {
    throw new Error('Invalid alpha value')
  }
  let _hex = hex
  if (hex.length === 4) {
    _hex = hex.replace(/\w{1}/g, '$&$&')
  }
  const r = parseInt(_hex.slice(1, 3), 16)
  const g = parseInt(_hex.slice(3, 5), 16)
  const b = parseInt(_hex.slice(5, 7), 16)
  if ([r, g, b].some(isNaN)) {
    throw new Error('Invalid hex color')
  }
  return `rgba(${r} ${g} ${b} / ${alpha * 100}%)`
}
