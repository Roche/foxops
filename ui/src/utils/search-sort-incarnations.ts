import { searchBy } from '.'
import { IncarnationsSortBy } from '../interfaces/incarnations.type'
import { IncarnationBase } from '../services/incarnations'
const mergeIncarnations = (a: IncarnationBase[], b: IncarnationBase[]) => {
  const result = [...a]
  b.forEach(x => {
    const index = result.findIndex(y => y.id === x.id)
    if (index === -1) {
      result.push(x)
    }
  })
  return result
}

interface SearchSortIncarnationsOptions {
  search: string
  sort: IncarnationsSortBy
  asc: boolean
}

export const searchSortIncarnations = (incarnations: IncarnationBase[], { search, sort, asc }: SearchSortIncarnationsOptions) => {
  const filteredData = Array.isArray(incarnations)
    ? incarnations.filter(searchBy<Partial<IncarnationBase>>(search, ['id', 'incarnationRepository', 'targetDirectory']))
    : []
  const sortFunc = (a: IncarnationBase, b: IncarnationBase) => {
    if (asc) {
      return a[sort].localeCompare(b[sort])
    }
    return b[sort].localeCompare(a[sort])
  }
  try {
    const searchRegex = new RegExp(search, 'i')
    const regexFilteredData = Array.isArray(incarnations)
      ? incarnations.filter(x => x.id.toString().match(searchRegex)
        || x.incarnationRepository.match(searchRegex)
        || x.targetDirectory.match(searchRegex))
      : []
    const _data = mergeIncarnations(filteredData, regexFilteredData)
    return _data.sort(sortFunc)
  } catch (error) {
    // invalid regex
  }
  return filteredData.sort(sortFunc)
}
