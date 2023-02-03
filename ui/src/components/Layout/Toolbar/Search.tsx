import { useQueries, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Incarnation, incarnations } from '../../../services/incarnations'
import { useIncarnationsSortStore } from '../../../stores/incarnations-sort'
import { useToolbarSearchStore } from '../../../stores/toolbar-search'
import { searchSortIncarnations } from '../../../utils/search-sort-incarnations'
import { Button } from '../../common/Button/Button'
import { Hug } from '../../common/Hug/Hug'
import { Download } from '../../common/Icons/Download'
import { Pause } from '../../common/Icons/Pause'
import { TextField } from '../../common/TextField/TextField'
import { Tooltip } from '../../common/Tooltip/Tooltip'

const PARALLEL_REQUESTS = 5

export const Search = () => {
  const { search, setSearch } = useToolbarSearchStore()
  const { data } = useQuery(['incarnations'], incarnations.get)
  const { sort, asc } = useIncarnationsSortStore()
  const _data = searchSortIncarnations(data || [], { search, sort, asc })

  const results = search ? `${_data.length} result${_data.length === 1 ? '' : 's'}` : ''

  const showFetchStatusButton = search && _data.length > 0

  const incarnationIds = _data.map(x => x.id)
  const [requested, setRequested] = useState<number[]>([])
  const [limit, setLimit] = useState(0)
  const handleRequestStatuses = () => {
    if (requested.length) {
      // cancel requests
      setRequested([])
      setLimit(0)
      return
    }
    setRequested(incarnationIds)
    setLimit(PARALLEL_REQUESTS)
  }
  const statusReceived = (id: number) => {
    setRequested(x => {
      const result = x.filter(y => y !== id)
      if (!result.length) {
        setLimit(0)
      }
      return result
    })
  }

  const queryClient = useQueryClient()
  useQueries({
    queries: requested.map((id, index) => ({
      queryKey: ['incarnations', id],
      queryFn: () => incarnations.getById(id),
      onSuccess: () => statusReceived(id),
      onError: () => {
        // isError doesn't appear in the IncarnationStatus component, 
        // so we need to manually set it to true
        // basically, directly it's not possible, 
        // instead of it there is a workaround:
        // we set templateRepository to null to show the error tag 🤷‍♂️
        statusReceived(id)
        let data: Incarnation | undefined = queryClient.getQueryData(['incarnations', id])
        if (!data) {
          data = ((queryClient.getQueryData(['incarnations']) || []) as Incarnation[])
            .find(x => x.id === id)
        }
        queryClient.setQueryData(['incarnations', id], {
          ...data,
          templateRepository: null
        })
      },
      enabled: index < limit
    }))
  })
  return (
    <Hug flex={['aic']}>
      <Hug mr={8}>
        {results}
      </Hug>
      {showFetchStatusButton && (
        <Hug mr={8}>
          <Tooltip style={{ zIndex: 13 }} title={limit > 0 ? 'Stop getting statuses' : 'Get statuses of found incarnations'}>
            <Button
              style={{ padding: 0, width: 38 }}
              onClick={handleRequestStatuses}>
              {limit > 0 ? <Pause width={20} height={20} /> : <Download width={20} height={20} />}
            </Button>
          </Tooltip>
        </Hug>
      )}
      <Hug allw={300}>
        <TextField
          placeholder="Search..."
          type="search"
          value={search}
          onChange={e => setSearch(e.target.value)} />
      </Hug>
    </Hug>
  )
}
