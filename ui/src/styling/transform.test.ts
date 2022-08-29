import { buildTransform } from './transform'

it('builds a transform string', () => {
  expect(buildTransform({ translate: { x: 10, y: 20 }, scale: 1.5 })).toBe('translate(10px, 20px) scale(1.5)')
  expect(buildTransform({ translate: 10, scale: 1.5 })).toBe('translate(10px) scale(1.5)')
  expect(buildTransform({ translate: '-50%, -50%', scale: 1.5 })).toBe('translate(-50%, -50%) scale(1.5)')
  expect(buildTransform()).toBe('none')
})
