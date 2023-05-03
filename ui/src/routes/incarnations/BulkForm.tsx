import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm, SubmitHandler, Controller } from 'react-hook-form'
import { Button } from '../../components/common/Button/Button'
import { Hug } from '../../components/common/Hug/Hug'
import { TextField } from '../../components/common/TextField/TextField'
import { incarnations } from '../../services/incarnations'
import { useIncarnationsOperations } from '../../stores/incarnations-operations'
import { ToggleSwitch } from '../../components/common/ToggleSwitch/ToggleSwitch'
import { Incarnation } from 'interfaces/incarnations.types'

export const BulkForm = () => {
  const { register, handleSubmit, control, formState: { errors } } = useForm({
    defaultValues: {
      templateVersion: '',
      automerge: true
    }
  })

  const { selectedIncarnations } = useIncarnationsOperations()
  const queryClient = useQueryClient()
  const { mutateAsync: update } = useMutation(
    ({
      incarnation,
      templateVersion,
      automerge
    }: {
      incarnation: Incarnation,
      templateVersion: string,
      automerge: boolean
    }) => incarnations.updateTemplateVersion(incarnation, { templateVersion, automerge })
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

  const onSubmit: SubmitHandler<{ templateVersion: string, automerge: boolean }> = async values => {
    const ids = selectedIncarnations.map(x => x.id)
    startUpdate(ids)
    const updates: Promise<void>[] = []
    for (const x of selectedIncarnations) {
      updates.push(
        update({
          incarnation: x,
          ...values
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
      <Hug mb={16}>
        <TextField
          autoFocus
          label="Template version"
          disabled={updating}
          size="large"
          hasError={!!errors.templateVersion}
          required
          {...register('templateVersion', { required: true })} />
      </Hug>
      <Hug mb={16}>
        <Controller
          control={control}
          name="automerge"
          render={({ field: { onChange, value } }) => (
            <ToggleSwitch checked={value} label="Automerge" onChange={e => onChange(e.target.checked)} />
          )} />
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
