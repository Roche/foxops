import { transparentize } from './colors'

const wrap = (hex: string, alpha: number) => () => transparentize(hex, alpha)

test('transparentize should throw error if the inputs are invalid', () => {
  expect(wrap('#fff', -0.1)).toThrow('Invalid alpha value')
  expect(wrap('#fff', 1.1)).toThrow('Invalid alpha value')
  expect(wrap('red', 0.7)).toThrow('Invalid hex color')
  expect(wrap('#fffffff', 0.7)).toThrow('Invalid hex color')
  expect(wrap('#ggg', 0.7)).toThrow('Invalid hex color')
})

test('transparentize should convert hex to rgba value with appropriate alpha', () => {
  expect(transparentize('#fff', .1)).toBe('rgba(255 255 255 / 10%)')
  expect(transparentize('#f5f5f5', .7)).toBe('rgba(245 245 245 / 70%)')
})

