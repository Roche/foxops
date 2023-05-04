import { useIsFetching, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { ErrorTag, StatusTag } from '.'
import { Button } from '../../../components/common/Button/Button'
import { Hug } from '../../../components/common/Hug/Hug'
import { IconButton } from '../../../components/common/IconButton/IconButton'
import { Download } from '../../../components/common/Icons/Download'
import { Minus } from '../../../components/common/Icons/Minus'
import { Plus } from '../../../components/common/Icons/Plus'
import { Tooltip } from '../../../components/common/Tooltip/Tooltip'
import { incarnations } from '../../../services/incarnations'
import { useIncarnationsOperations } from '../../../stores/incarnations-operations'
import { useCanShowStatusStore } from '../../../stores/show-status'
import { Incarnation } from '../../../interfaces/incarnations.types'

export const IncarnationStatus = ({ id, size }: { id: number, size?: 'small' | 'large' }) => {
  const key = ['incarnations', id]
  const isFetching = !!useIsFetching({ queryKey: key })
  const queryClient = useQueryClient()
  const cached = queryClient.getQueryData<Incarnation>(key)

  const { refetch } = useQuery(
    ['incarnations', id],
    () => incarnations.getById(id),
    { enabled: false }
  )
  const [statusRequested, setStatusRequested] = useState(Number(!!cached))

  const handleGetStatus = () => {
    setStatusRequested(statusRequested + 1)
    if (statusRequested > 0) {
      refetch()
    }
  }

  const svgProps = size === 'small' ? { width: 16, height: 16 } : { width: 20, height: 20 }
  return (
    <>
      {(!!cached || !!statusRequested) && <Status id={id} key={statusRequested} incarnation={cached} />}
      <Hug mr={4}>
        <Tooltip title={isFetching ? 'Getting status...' : 'Get status'} style={{ whiteSpace: 'nowrap' }}>
          <Button size={size} loading={isFetching} onClick={handleGetStatus}>
            {!isFetching && <Download {...svgProps} />}
          </Button>
        </Tooltip>
      </Hug>
    </>
  )
}

const Status = ({ id, incarnation }: { id: number, incarnation?: Incarnation }) => {
  const { data, isError, isSuccess } = useQuery(
    ['incarnations', id],
    () => incarnations.getById(id),
    {
      refetchOnWindowFocus: false,
      staleTime: Infinity
    }
  )
  const _incarnation = data || incarnation
  const failed = _incarnation?.templateRepository === null
  const canShowInc = !!(_incarnation && isSuccess && !failed)
  const { select, deselect, selectedIncarnations } = useIncarnationsOperations()
  const selected = selectedIncarnations.some(x => x.id === _incarnation?.id)
  const handleClick = () => {
    if (!_incarnation) return
    if (selected) {
      deselect(_incarnation)
      return
    }
    select(_incarnation)
  }
  const { setCanShow } = useCanShowStatusStore()
  useEffect(() => {
    if (!isSuccess) return
    setCanShow(true)
  }, [isSuccess, setCanShow])
  return (
    <>
      <Hug mr={4}>
        {isError || failed ? <ErrorTag>error</ErrorTag> : ''}
        {canShowInc ? <StatusTag mergeRequestStatus={_incarnation.mergeRequestStatus} /> : ''}
      </Hug>
      {canShowInc && (
        <Hug mr={4}>
          <Tooltip title={selected ? 'Remove from bulk update' : 'Add to bulk update'}>
            <IconButton size="medium" onClick={handleClick}>
              {selected ? <Minus /> : <Plus />}
            </IconButton>
          </Tooltip>
        </Hug>
      )}
    </>
  )
}
