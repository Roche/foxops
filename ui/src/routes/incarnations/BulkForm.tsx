import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, SubmitHandler } from 'react-hook-form'
import { Button } from '../../components/common/Button/Button'
import { Hug } from '../../components/common/Hug/Hug'
import { TextField } from '../../components/common/TextField/TextField'
import { Incarnation, incarnations } from '../../services/incarnations'
import { useIncarnationsOperations } from '../../stores/incarnations-operations'

export const BulkForm = () => {
  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: {
      templateVersion: ''
    }
  })

  const { selectedIncarnations } = useIncarnationsOperations()
  const queryClient = useQueryClient()
  const { mutateAsync: update } = useMutation(
    ({
      incarnation,
      templateVersion
    }: {
      incarnation: Incarnation,
      templateVersion: string
    }) => incarnations.updateTemplateVersion(incarnation, templateVersion)
  )
  const {
    startUpdate,
    updatingIds,
    updateSucceed,
    updateFailed,
    deselect,
    select,
    updatedIds,
    failedUpdatedIds
  } = useIncarnationsOperations()

  const onSubmit: SubmitHandler<{ templateVersion: string }> = async ({ templateVersion }) => {
    const ids = selectedIncarnations.map(x => x.id)
    startUpdate(ids)
    const updates: Promise<void>[] = []
    for (const x of selectedIncarnations) {
      updates.push(
        update({
          incarnation: x,
          templateVersion
        })
          .then(updated => {
            console.log('success', updated)
            queryClient.setQueryData(['incarnations', x.id], updated)
            updateSucceed(updated.id)
            deselect(updated)
            select(updated)
          })
          .catch(() => {
            updateFailed(x.id)
          })
      )
    }
  }
  const updating = updatingIds.length !== updatedIds.length + failedUpdatedIds.length
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Hug mb={8}>
        <TextField
          autoFocus
          label="Template version"
          disabled={updating}
          size="large"
          hasError={!!errors.templateVersion}
          required
          {...register('templateVersion', { required: true })} />
      </Hug>
      <Hug flex={['jcfe', 'aic']}>
        <Hug>
          <Button
            loading={updating}
            disabled={updating}
            style={{ minWidth: 120 }}
            type="submit">
            Update
          </Button>
        </Hug>
      </Hug>
    </form>
  )
}
