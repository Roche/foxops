export const delay = (ms: number) => new Promise(resolve => {
  setTimeout(resolve, ms)
})

export const searchBy = <T extends Record<string, unknown>>(query: string, fields: (string | undefined)[]) => {
  const search = (object: T) => {
    const values = fields.map(field => {
      if (!field) return ''
      const value = object[field]
      return typeof value === 'string' || typeof value === 'number'
        ? value.toString().toLowerCase()
        : ''
    })
    const string = values.join(' ')
    return string.includes(query.toLowerCase())
  }
  return search
}
