import styled from '@emotion/styled'
import React from 'react'

type OffsetPropsKeys = 'm' | 'my' | 'mx' | 'mt' | 'ml' | 'mr' | 'mb' | 'p' | 'py' | 'px' | 'pt' | 'pr' | 'pb' | 'pl'

type OffsetPropDimension = 'top' | 'bottom' | 'left' | 'right'

const offsetPropDimensions: Capitalize<OffsetPropDimension>[] = ['Top', 'Bottom', 'Left', 'Right']

export type OffsetPropName = 'margin' | 'padding'
type OffsetPropNames = `${OffsetPropName}${Capitalize<OffsetPropDimension>}` | OffsetPropName

interface CreateOffsetPropOptions {
  name: OffsetPropName,
  full?: string | number,
  vertical?: string | number,
  horizontal?: string | number,
  top?: string | number,
  bottom?: string | number,
  left?: string | number,
  right?: string | number,
}

export const addPoints = (x?: string | number) => typeof x === 'string' && parseFloat(x) !== +x ? x : `${x || 0}px`

export const checkPropValue = (x?: string | number) => typeof x === 'string' || typeof x === 'number'

type CreateOffsetPropResult = Partial<{
  [key in OffsetPropNames]: string
}>

export const createOffsetProp = ({
  name,
  full,
  vertical,
  horizontal,
  top,
  bottom,
  left,
  right
}: CreateOffsetPropOptions): CreateOffsetPropResult => {
  const fullProp = checkPropValue(full) ? addPoints(full) : undefined
  const verticalProp = checkPropValue(vertical) ? addPoints(vertical) : fullProp
  const horizontalProp = checkPropValue(horizontal) ? addPoints(horizontal) : fullProp
  const topProp = checkPropValue(top) ? addPoints(top) : verticalProp
  const bottomProp = checkPropValue(bottom) ? addPoints(bottom) : verticalProp
  const leftProp = checkPropValue(left) ? addPoints(left) : horizontalProp
  const rightProp = checkPropValue(right) ? addPoints(right) : horizontalProp
  const props = [topProp, bottomProp, leftProp, rightProp]
  if (props.every(checkPropValue)) {
    if (props.every(x => x === topProp)) {
      return { [name]: topProp }
    }
    if (topProp === bottomProp && leftProp === rightProp) {
      return { [name]: `${topProp} ${leftProp}` }
    }
    if (leftProp === rightProp) {
      return { [name]: `${topProp} ${leftProp} ${bottomProp}` }
    }
    return { [name]: `${topProp} ${rightProp} ${bottomProp} ${leftProp}` }
  }
  return props.reduce((acc, prop, index) => {
    if (checkPropValue(prop)) {
      acc[`${name}${offsetPropDimensions[index]}`] = prop
    }
    return acc
  }, {} as CreateOffsetPropResult)
}

type FlexOptions = 'inline'
  | 'fdr' | 'fdrr' | 'fxdc' | 'fxdcr'
  | 'fxww' | 'fxwnw'
  | 'jcfs' | 'jcfe' | 'jcc' | 'jcsb' | 'jcsa'
  | 'aifs' | 'aife' | 'aic' | 'ais' | 'aib'
type FlexCSSProps = {
  display?: 'flex' | 'inline-flex',
  flexDirection?: 'row' | 'row-reverse' | 'column' | 'column-reverse',
  flexWrap?: 'wrap' | 'nowrap',
  justifyContent?: 'flex-start' | 'flex-end' | 'center' | 'space-between' | 'space-around',
  alignItems?: 'flex-start' | 'flex-end' | 'center' | 'stretch' | 'baseline'
}

const flexOptionsMap = new Map([
  ['inline', { display: 'inline-flex' }],
  ['fdr', { flexDirection: 'row' }],
  ['fdrr', { flexDirection: 'row-reverse' }],
  ['fxdc', { flexDirection: 'column' }],
  ['fxdcr', { flexDirection: 'column-reverse' }],
  ['fxww', { flexWrap: 'wrap' }],
  ['fxwnw', { flexWrap: 'nowrap' }],
  ['jcfs', { justifyContent: 'flex-start' }],
  ['jcfe', { justifyContent: 'flex-end' }],
  ['jcc', { justifyContent: 'center' }],
  ['jcsb', { justifyContent: 'space-between' }],
  ['jcsa', { justifyContent: 'space-around' }],
  ['aifs', { alignItems: 'flex-start' }],
  ['aife', { alignItems: 'flex-end' }],
  ['aic', { alignItems: 'center' }],
  ['ais', { alignItems: 'stretch' }],
  ['aib', { alignItems: 'baseline' }]
])
export const createFlexOptions = (options?: boolean | FlexOptions[]): FlexCSSProps => {
  if (typeof options === 'undefined') return {}
  if (typeof options === 'boolean') {
    return {
      display: 'flex'
    }
  }
  return options.reduce((acc, option) => {
    const flexOptions = flexOptionsMap.get(option)
    if (flexOptions) {
      Object.assign(acc, flexOptions)
    }
    return acc
  }, { display: 'flex' } as FlexCSSProps)
}

interface WidthOptions {
  miw?: string | number,
  maw?: string | number,
  w?: string | number,
  allw?: string | number,
}

export const createWidthOptions = (options: WidthOptions) => {
  const { miw, maw, w, allw } = options
  const allWidth = checkPropValue(allw) ? addPoints(allw) : undefined
  const width = checkPropValue(w) ? addPoints(w) : allWidth
  const minWidth = checkPropValue(miw) ? addPoints(miw) : allWidth
  const maxWidth = checkPropValue(maw) ? addPoints(maw) : allWidth
  return { width, minWidth, maxWidth }
}

interface BoxProps extends Partial<Record<OffsetPropsKeys, string | number>>, WidthOptions {
  flex?: boolean | FlexOptions[]
}

const Box = styled(
  'div'
)((props: BoxProps) => ({
  ...createOffsetProp({ name: 'margin', full: props.m, vertical: props.my, horizontal: props.mx, top: props.mt, bottom: props.mb, left: props.ml, right: props.mr }),
  ...createOffsetProp({ name: 'padding', full: props.p, vertical: props.py, horizontal: props.px, top: props.pt, bottom: props.pb, left: props.pl, right: props.pr }),
  ...createFlexOptions(props.flex),
  ...createWidthOptions({ w: props.w, miw: props.miw, maw: props.maw, allw: props.allw })
}))

interface HugProps extends Partial<Record<OffsetPropsKeys, string | number>>, React.HTMLAttributes<HTMLDivElement>, WidthOptions {
  children?: React.ReactNode,
  as?: React.ElementType,
  flex?: boolean | FlexOptions[],
}

export const Hug = ({ children, as = 'div', flex, miw, maw, w, allw, ...rest }: HugProps) => (
  <Box
    as={as}
    className="Hug"
    flex={flex}
    miw={miw}
    maw={maw}
    w={w}
    allw={allw}
    {...rest}>
    {children}
  </Box>
)
