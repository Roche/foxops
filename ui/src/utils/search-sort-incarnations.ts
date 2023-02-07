import { searchBy } from '.'
import { IncarnationsSortBy } from '../interfaces/incarnations.type'
import { IncarnationBase } from '../services/incarnations'
import * as semver from 'semver'

function semverRegex() {
  return /(?<=^v?|\sv?)(?:(?:0|[1-9]\d{0,9}?)\.){2}(?:0|[1-9]\d{0,9})(?:-(?:--+)?(?:0|[1-9]\d*|\d*[a-z]+\d*)){0,100}(?=$| |\+|\.)(?:(?<=-\S+)(?:\.(?:--?|[\da-z-]*[a-z-]\d*|0|[1-9]\d*)){1,100}?)?(?!\.)(?:\+(?:[\da-z]\.?-?){1,100}?(?!\w))?(?!\+)/gi
}

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
  const sortByStringField = (a: IncarnationBase, b: IncarnationBase) => {
    if (asc) {
      return a[sort].localeCompare(b[sort])
    }
    return b[sort].localeCompare(a[sort])
  }
  const sortBySemverField = (a: IncarnationBase, b: IncarnationBase) => {
    const sv1 = semverRegex().exec(a[sort])?.[0]
    const sv2 = semverRegex().exec(b[sort])?.[0]
    if (!sv1) {
      return 1
    }
    if (!sv2) {
      return -1
    }
    if (asc) {
      return semver.compare(sv1, sv2)
    }
    return semver.compare(sv2, sv1)
  }
  const sortFunc = sort === 'templateVersion'
    ? sortBySemverField
    : sortByStringField
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
