import { addPoints, checkPropValue, createFlexOptions, createOffsetProp, Hug, OffsetPropName } from './Hug'
import { render, screen } from '../../../support/setup-tests'

test('Hug:addPoints: adds points to the number or string', () => {
  expect(addPoints(1)).toBe('1px')
  expect(addPoints('1')).toBe('1px')
  expect(addPoints('1.1')).toBe('1.1px')
  expect(addPoints('1.1px')).toBe('1.1px')
  expect(addPoints('1.1em')).toBe('1.1em')
  expect(addPoints('1.1rem')).toBe('1.1rem')
  expect(addPoints('1.1%')).toBe('1.1%')
  expect(addPoints('1.1vw')).toBe('1.1vw')
  expect(addPoints('1.1vh')).toBe('1.1vh')
  expect(addPoints('1.1vmin')).toBe('1.1vmin')
  expect(addPoints('1.1vmax')).toBe('1.1vmax')
})

test('Hug:addPoints: returns 0px if its undefined', () => {
  expect(addPoints(undefined)).toBe('0px')
})

test('Hug:checkPropValue: returns true if its a string or number', () => {
  expect(checkPropValue('1')).toBe(true)
  expect(checkPropValue(1)).toBe(true)
  expect(checkPropValue(undefined)).toBe(false)
})

test('Hug:createOffsetProp: creates a margin or padding prop', () => {
  let result = createOffsetProp({
    name: 'margin' as OffsetPropName,
    full: 1
  })
  expect(result).toEqual({ margin: '1px' })
  result = createOffsetProp({
    name: 'margin' as OffsetPropName,
    vertical: 1
  })
  expect(result).toEqual({ marginTop: '1px', marginBottom: '1px' })
  result = createOffsetProp({
    name: 'margin' as OffsetPropName,
    horizontal: 1
  })
  expect(result).toEqual({ marginLeft: '1px', marginRight: '1px' })
  result = createOffsetProp({
    name: 'margin' as OffsetPropName,
    top: 1,
    bottom: 2,
    left: 3,
    right: 3
  })
  expect(result).toEqual({ margin: '1px 3px 2px' })
  result = createOffsetProp({
    name: 'padding' as OffsetPropName,
    horizontal: 2,
    top: 1
  })
  expect(result).toEqual({ paddingTop: '1px', paddingLeft: '2px', paddingRight: '2px' })
  result = createOffsetProp({
    name: 'padding' as OffsetPropName,
    vertical: 2,
    right: 1
  })
  expect(result).toEqual({ paddingTop: '2px', paddingBottom: '2px', paddingRight: '1px' })
})

test('Hug:createFlexOptions should create appropriate CSS flex value', () => {
  let result = createFlexOptions()
  expect(result).toEqual({})
  result = createFlexOptions(true)
  expect(result).toEqual({ display: 'flex' })
  result = createFlexOptions(['inline', 'aic', 'jcsb', 'fxwnw'])
  expect(result).toEqual({ display: 'inline-flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'nowrap' })
})

test('Hug should render as section tag with 5px padding and 10vh margin-top', () => {
  render(<Hug data-testid="Hug" p={5} mt="10vh" as="section" flex={['aic', 'jcsb']}>Test hug</Hug>)
  const hug = screen.getByTestId('Hug')
  expect(hug).toHaveStyle({
    padding: '5px',
    marginTop: '10vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between'
  })
  expect(hug.tagName).toBe('SECTION')
})
