import { Paths } from 'shared/types'
import { searchBy } from '.'
import { IncarnationBase } from '../interfaces/incarnations.types'
import { INCARNATION_SEARCH_FIELDS } from '../services/incarnations'
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

export const makeSortBySemVer = (semVerField: Paths<IncarnationBase>) => (a: IncarnationBase, b: IncarnationBase) => {
  const valA = semVerField.split('.').reduce((p: any, c: string) => p && p[c] || null, a)  // eslint-disable-line
  const valB = semVerField.split('.').reduce((p: any, c: string) => p && p[c] || null, b)  // eslint-disable-line

  if (typeof valA !== 'string' || typeof valB !== 'string') return 1
  const sv1 = semverRegex().exec(valA)?.[0]
  const sv2 = semverRegex().exec(valB)?.[0]

  if (!valA) {
    return 1
  }
  if (!valB) {
    return -1
  }
  if (sv1 && sv2) {
    return semver.compare(sv1, sv2)
  }
  return a.templateVersion.localeCompare(b.templateVersion)
}

interface SearchIncarnationOptions {
  search: string
}

export const searchIncarnations = (incarnations: IncarnationBase[], { search }: SearchIncarnationOptions) => {
  const filteredData = Array.isArray(incarnations)
    ? incarnations.filter(searchBy<Partial<IncarnationBase>>(search, INCARNATION_SEARCH_FIELDS))
    : []
  try {
    const searchRegex = new RegExp(search, 'i')
    const regexFilteredData = Array.isArray(incarnations)
      ? incarnations.filter(x => x.id.toString().match(searchRegex)
        || x.incarnationRepository.match(searchRegex)
        || x.targetDirectory.match(searchRegex))
      : []
    const _data = mergeIncarnations(filteredData, regexFilteredData)
    return _data
  } catch (error) {
    // invalid regex
  }
  return filteredData
}
