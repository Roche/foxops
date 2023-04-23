import { QueryKey, useQueryClient } from '@tanstack/react-query'
import { useMemo } from 'react'
import { useToolbarSearchStore } from '../stores/toolbar-search'
import { useIncarnationsQuery } from '../services/incarnations'
import { searchIncarnations } from '../utils/search-incarnations'
import { Incarnation, IncarnationBase } from '../interfaces/incarnations.types'

const getSingleIncarnations = (queriesData: Array<[QueryKey, unknown]>) => {
  const singleIncarnationsMap = new Map<number, Incarnation>()
  queriesData.forEach(([, x]) => {
    const _x = x as Incarnation | undefined
    if (!_x) return
    singleIncarnationsMap.set(_x.id, _x)
  })
  return singleIncarnationsMap
}

export const useIncarnationsData = () => {
  const { data, isSuccess } = useIncarnationsQuery()

  const queryClient = useQueryClient()
  const queryCache = queryClient.getQueryCache()
  const queriesData = queryCache
    .findAll(['incarnations'])
    .filter(x => x.queryKey[0] === 'incarnations' && x.queryKey.length === 2) // get single incarnation queries cache
    .map(x => [x.queryKey, x.state.data] as [QueryKey, unknown])

  const singleIncarnationsMap = useMemo(() => getSingleIncarnations(queriesData), [queriesData])

  const { search } = useToolbarSearchStore()

  const memoizedData = useMemo(
    () => {
      const result = isSuccess
        ? data.map(x => singleIncarnationsMap.has(x.id)
          ? {
            ...x,
            templateVersion: singleIncarnationsMap.get(x.id)?.templateRepositoryVersion || undefined
          } as IncarnationBase
          : x
        )
        : [] as IncarnationBase[]
      return searchIncarnations(result || [], { search })
    }
    , [data, isSuccess, singleIncarnationsMap.size, search])
  return memoizedData
}
