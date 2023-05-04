const PREFIX = 'foxops-store'

export const getStorage = () => sessionStorage // will be changed to localStorage

export const createStorageKey = (key: string) => `${PREFIX}-${key}`

export const STORAGE_KEYS = {
  AUTH: createStorageKey('auth'),
  THEME: createStorageKey('theme'),
  TABLE: createStorageKey('table')
}
