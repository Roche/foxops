export const delay = (ms: number) => new Promise(resolve => {
  setTimeout(resolve, ms)
})

export const searchBy = <T extends Record<string, unknown>>(query: string, fields: string[]) => {
  const search = (object: T) => {
    const values = fields.map(field => {
      const value = object[field]
      return typeof value === 'string' ? value.toLowerCase() : ''
    })
    const string = values.join(' ')
    return string.toLowerCase().includes(query.toLowerCase())
  }
  return search
}
