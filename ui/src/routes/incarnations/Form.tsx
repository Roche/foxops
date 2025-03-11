import { useForm, SubmitHandler, Controller } from 'react-hook-form'
import { Button } from '../../components/common/Button/Button'
import { Hug } from '../../components/common/Hug/Hug'
import { IconButton } from '../../components/common/IconButton/IconButton'
import { TextField } from '../../components/common/TextField/TextField'
import { Section, StatusTag } from './parts'
import { IncarnationInput } from '../../services/incarnations'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ApiErrorResponse } from '../../services/api'
import { delay } from '../../utils'
import { useMemo, useState } from 'react'
import styled from '@emotion/styled'
import { Tooltip } from '../../components/common/Tooltip/Tooltip'
import { IncarnationLinks } from './parts/IncarnationLinks'
import isUrl from 'is-url'
import { OpenInNew } from '../../components/common/Icons/OpenInNew'
import { ToggleSwitch } from '../../components/common/ToggleSwitch/ToggleSwitch'
import {
  IncarnationApiView,
  MergeRequestStatus
} from 'interfaces/incarnations.types'
import { JsonEditor } from 'components/common/JsonEditor/JsonEditor'
import { Tabs } from 'components/common/Tabs/Tabs'
import { useNavigate } from 'react-router-dom'
import { Dialog } from 'components/common/Dialog/Dialog'
import { useErrorStore } from 'stores/error'

const DeleteIncarnationLink = styled.span`
  cursor: pointer;
  text-decoration: underline;
`

export type DiffChanges = {
  added: number,
  removed: number
}

type FormProps = {
  mutation: (data: IncarnationInput) => Promise<IncarnationApiView>,
  deleteIncarnation?: () => Promise<void>,
  resetIncarnation?: () => Promise<void>,
  defaultValues: IncarnationInput,
  diffChanges?: DiffChanges,
  isEdit?: boolean,
  incarnationMergeRequestStatus?: MergeRequestStatus | null,
  mergeRequestUrl?: string | null,
  commitUrl?: string,
  templateDataFull?: Record<string, never>
}

type ChangeSquareProps = {
  color: 'green' | 'red' | 'gray';
};

const changeColors = {
  green: '#2c9c69',
  red: '#d73a49',
  gray: '#6a737d'
} as const

const ChangeSquare = ({ color }: ChangeSquareProps) => {
  let hexCode = ''

  if (color === 'green') {
    hexCode = changeColors.green
  } else if (color === 'red') {
    hexCode = changeColors.red
  } else {
    hexCode = changeColors.gray
  }

  const Box = styled.div({
    width: 12,
    height: 12,
    backgroundColor: hexCode,
    display: 'inline-block',
    marginRight: 1,
    marginLeft: 1
  })

  return <Box />
}

const calculateNumberOfBlocks = (diffChanges: DiffChanges | undefined) => {
  if (diffChanges === undefined) return { green: 0, red: 0, gray: 0 }

  if (diffChanges.added === 0 && diffChanges.removed === 0) return { green: 0, gray: 5, red: 0 }
  if (diffChanges.added === 0 && diffChanges.removed > 0) return { green: 0, gray: 0, red: 5 }
  if (diffChanges.added > 0 && diffChanges.removed === 0) return { green: 5, red: 0, gray: 0 }

  const addRemovePercentage
    = diffChanges.added / (diffChanges.removed + diffChanges.added)

  if (addRemovePercentage < 0.15) return { red: 4, green: 1, gray: 0 }
  if (addRemovePercentage < 0.35) return { red: 3, green: 2, gray: 0 }
  if (addRemovePercentage > 0.65) return { red: 2, green: 3, gray: 0 }
  if (addRemovePercentage > 0.85) return { red: 1, green: 4, gray: 0 }

  return { red: 2, green: 2, gray: 1 }
}

const Added = styled.span({
  color: changeColors.green,
  margin: 2
})

const Removed = styled.span({
  color: changeColors.red,
  margin: 2
})

export const IncarnationsForm = ({
  mutation,
  defaultValues,
  diffChanges,
  isEdit,
  deleteIncarnation = () => Promise.resolve(),
  resetIncarnation = () => Promise.resolve(),
  incarnationMergeRequestStatus,
  mergeRequestUrl,
  commitUrl,
  templateDataFull
}: FormProps) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
    control,
    watch
  } = useForm({
    defaultValues
  })
  const templateRepo = watch('templateRepository')
  const failed = templateRepo === '' && isEdit
  const navigate = useNavigate()

  const errorStore = useErrorStore()

  const queryClient = useQueryClient()
  const { mutateAsync, isLoading } = useMutation(mutation)
  const deleteMutation = useMutation(deleteIncarnation)

  const resetMutation = useMutation(resetIncarnation)

  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [resetDialogOpen, setResetDialogOpen] = useState(false)

  const onDelete = async () => {
    setDeleteDialogOpen(false)
    try {
      await deleteMutation.mutateAsync()
      await delay(1000)
      queryClient.invalidateQueries(['incarnations'])
      navigate('/incarnations')
    } catch (error) {
      errorStore.setError(error as ApiErrorResponse)
    }
  }

  const onReset = async () => {
    setResetDialogOpen(false)
    try {
      await resetMutation.mutateAsync()
    } catch (error) {
      errorStore.setError(error as ApiErrorResponse)
    }
  }

  const onSubmit: SubmitHandler<IncarnationInput> = async incarnation => {
    errorStore.clearError()
    try {
      console.log(incarnation)
      await mutateAsync(incarnation)
      await delay(1000)
      queryClient.invalidateQueries(['incarnations'])
      navigate('/incarnations')
    } catch (err) {
      const error = err as ApiErrorResponse
      errorStore.setError(error)
    }
  }
  const buttonTitle = isEdit
    ? isLoading
      ? 'Updating'
      : 'Update'
    : isLoading
      ? 'Creating'
      : 'Create'

  const deleteButtonTitle = deleteMutation.isSuccess
    ? 'Deleted!'
    : deleteMutation.isLoading
      ? 'Deleting'
      : 'Delete'

  const resetButtonTitle = resetMutation.isSuccess
    ? 'Reset!'
    : resetMutation.isLoading
      ? 'Resetting'
      : 'Reset'

  const resetIncarnationEnabled = diffChanges && (diffChanges.added !== 0 || diffChanges.removed !== 0)

  const editTemplateDataController = (
    <Controller
      control={control}
      name="templateData"
      rules={{
        validate: value => {
          try {
            JSON.parse(value)
            return true
          } catch (error) {
            return 'Invalid JSON'
          }
        }
      }}
      render={({
        field: { onChange, value },
        fieldState: { error, invalid }
      }) => (
        <JsonEditor
          defaultValue={value}
          onChange={onChange}
          invalid={invalid}
          error={error?.message}
          height="100%"
        />
      )}
    />
  )

  const numberOfBlocks = useMemo(
    () => calculateNumberOfBlocks(diffChanges),
    [diffChanges]
  )

  const form = (
    <Hug as="form" h="100%" flex onSubmit={handleSubmit(onSubmit)}>
      <Hug w="100%" miw={600} px={8} pt={32} h="100%" flex={['fxdc']}>
        <Hug flex={['jcsb']} h="80%">
          <Hug w="40%" h="100%">
            <Hug mb={16}>
              <TextField
                autoFocus
                label="Incarnation repository"
                disabled={isLoading || isEdit}
                size="large"
                hasError={!!errors.repository}
                required
                {...register('repository', { required: true })}
              />
            </Hug>
            <Hug mb={16}>
              <TextField
                label="Target directory"
                size="large"
                disabled={isLoading || isEdit}
                hasError={!!errors.targetDirectory}
                {...register('targetDirectory')}
              />
            </Hug>
            <Hug mb={16} flex={['aic']}>
              <Hug w="100%">
                <TextField
                  label="Template repository"
                  disabled={isLoading || isEdit}
                  size="large"
                  hasError={!!errors.templateRepository}
                  required
                  {...register('templateRepository', { required: true })}
                />
              </Hug>
              {isUrl(templateRepo) && (
                <Hug ml={8}>
                  <Tooltip title="Open in new tab">
                    <a
                      style={{ display: 'block' }}
                      href={templateRepo}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <IconButton type="button">
                        <OpenInNew />
                      </IconButton>
                    </a>
                  </Tooltip>
                </Hug>
              )}
            </Hug>
            <Hug mb={16}>
              <TextField
                label="Template version"
                disabled={isLoading}
                size="large"
                hasError={!!errors.templateVersion}
                required
                {...register('templateVersion', { required: true })}
              />
            </Hug>
            {isEdit && (
              <Hug mb={16}>
                <Controller
                  control={control}
                  name="automerge"
                  render={({ field: { onChange, value } }) => (
                    <ToggleSwitch
                      checked={value}
                      label="Automerge"
                      disabled={isLoading}
                      onChange={e => onChange(e.target.checked)}
                    />
                  )}
                />
              </Hug>
            )}
          </Hug>
          <Hug w="calc(60% - 2rem)" h="100%">
            {isEdit ? (
              <Tabs
                tabs={[
                  {
                    label: <strong>Template data JSON</strong>,
                    content: (
                      <Hug my={8} h="100%">
                        {editTemplateDataController}
                      </Hug>
                    )
                  },
                  {
                    label: <strong>Full template data (readonly)</strong>,
                    content: (
                      <Hug my={8} h="100%">
                        <JsonEditor
                          defaultValue={JSON.stringify(
                            templateDataFull,
                            null,
                            2
                          )}
                          readOnly
                          height="100%"
                        />
                      </Hug>
                    )
                  }
                ]}
              />
            ) : (
              <>
                <strong>Template data JSON</strong>
                <Hug my={16} h="100%">
                  {editTemplateDataController}
                </Hug>
              </>
            )}
          </Hug>
        </Hug>
        <Hug flex={['jcfe', 'aic']} mt="auto">
          <Hug>
            <Button
              loading={isLoading}
              style={{ minWidth: 120 }}
              type="submit"
              disabled={isLoading}
            >
              {buttonTitle}
            </Button>
          </Hug>
        </Hug>
      </Hug>
    </Hug>
  )
  const failedFeedback = (
    <Hug as="form" mb={16} flex>
      <Hug w="60%" miw={600} px={8} pt={32}>
        It looks like this incarnation is not available anymore 😔. You can{' '}
        <DeleteIncarnationLink onClick={() => setDeleteDialogOpen(true)}>delete</DeleteIncarnationLink>{' '}
        it.
      </Hug>
    </Hug>
  )
  return (
    <Section>
      <Hug flex={['aic']} w="100%">
        <Hug flex={['aic', 'jcfe']} w="100%">
          {diffChanges && (
            <Hug flex={['aic']} mb={0}>
              <Added>+{diffChanges.added}</Added>{' '}
              <Removed>-{diffChanges.removed}</Removed>
              <Hug ml={8}>
                {Array.from({ length: numberOfBlocks.green }, (_, i) => (
                  <ChangeSquare key={i} color="green" />
                ))}
                {Array.from({ length: numberOfBlocks.red }, (_, i) => (
                  <ChangeSquare key={i} color="red" />
                ))}
                {Array.from({ length: numberOfBlocks.gray }, (_, i) => (
                  <ChangeSquare key={i} color="gray" />
                ))}
              </Hug>
            </Hug>
          )}
          {incarnationMergeRequestStatus && (
            <Hug ml={16}>
              <Tooltip title="Merge request status">
                <StatusTag
                  mergeRequestStatus={incarnationMergeRequestStatus ?? null}
                />
              </Tooltip>
            </Hug>
          )}
          {isEdit && (
            <Hug ml={16} flex={['aic']}>
              <IncarnationLinks
                mergeRequestUrl={mergeRequestUrl}
                commitUrl={commitUrl}
                size="large"
              />
              <Hug ml={4}>
                <Tooltip title="Remove all manual changes">
                  <Button
                    minWidth="6.5rem"
                    variant="warning"
                    disabled={
                      resetMutation.isLoading || resetMutation.isSuccess || !resetIncarnationEnabled || incarnationMergeRequestStatus === 'open'
                    }
                    loading={deleteMutation.isLoading}
                    onClick={() => setResetDialogOpen(true)}
                  >
                    {resetButtonTitle}
                  </Button>
                </Tooltip>
              </Hug>
              <Hug ml={4}>
                <Tooltip title="Delete incarnation">
                  <Button
                    minWidth="6.5rem"
                    variant="danger"
                    disabled={
                      deleteMutation.isLoading || deleteMutation.isSuccess
                    }
                    loading={deleteMutation.isLoading}
                    onClick={() => setDeleteDialogOpen(true)}
                  >
                    {deleteButtonTitle}
                  </Button>
                </Tooltip>
              </Hug>
            </Hug>
          )}
        </Hug>
        <Dialog open={deleteDialogOpen} onAbort={() => setDeleteDialogOpen(false)} onConfirm={onDelete} title="Delete incarnation">
          <span>Are you sure you want to delete this incarnation?</span>
          <span>This action <strong>cannot</strong> be undone.</span>
        </Dialog>
        <Dialog open={resetDialogOpen} onAbort={() => setResetDialogOpen(false)} onConfirm={onReset} title="Reset incarnation">
          <span>Are you sure you want to reset this incarnation?</span>
          <span>Doing this will create a merge request which removes all changes manually applied to the incarnation</span>
          <span>The merge request will not be automatically merged</span>
        </Dialog>
      </Hug>
      {failed ? (
        failedFeedback
      ) : (
        <Hug flex={['fxdc']} w="100%" h="calc(100% - 2rem)">
          {form}
        </Hug>
      )}
    </Section>
  )
}
