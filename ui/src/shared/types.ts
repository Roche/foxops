export type ThemeMode = 'light' | 'dark'

export type Paths<T> = T extends object ? { [K in keyof T]:
    `${Exclude<K, symbol>}${'' | `.${Paths<T[K]>}`}`
  }[keyof T] : never
