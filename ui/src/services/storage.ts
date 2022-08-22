const PREFIX = 'foxops-store'

export const getStorage = () => sessionStorage // will be changed to localStorage

export const createStorageKey = (key: string) => `${PREFIX}-${key}`

export const STORAGE_KEYS = {
  AUTH: createStorageKey('auth'),
  THEME: createStorageKey('theme')
}

export const getAuthToken = () => {
  const data = getStorage().getItem(STORAGE_KEYS.AUTH)
  if (!data) return null
  try {
    return JSON.parse(data).token
  } catch (error) {
    console.warn('No token found in storage')
    return null
  }
}
