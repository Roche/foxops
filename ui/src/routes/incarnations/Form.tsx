import { useForm, SubmitHandler, Controller } from 'react-hook-form'
import isEqual from 'lodash.isequal'
import { useNavigate } from 'react-router-dom'
import { Button } from '../../components/common/Button/Button'
import { Hug } from '../../components/common/Hug/Hug'
import { IconButton } from '../../components/common/IconButton/IconButton'
import { ExpandLeft } from '../../components/common/Icons/ExpandLeft'
import { TextField } from '../../components/common/TextField/TextField'
import { Section, StatusTag } from './parts'
import { IncarnationInput } from '../../services/incarnations'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ApiErrorResponse } from '../../services/api'
import { delay } from '../../utils'
import { useState } from 'react'
import styled from '@emotion/styled'
import { Close } from '../../components/common/Icons/Close'
import { Tooltip } from '../../components/common/Tooltip/Tooltip'
import { IncarnationLinks } from './parts/IncarnationLinks'
import isUrl from 'is-url'
import { OpenInNew } from '../../components/common/Icons/OpenInNew'
import { ToggleSwitch } from '../../components/common/ToggleSwitch/ToggleSwitch'
import { IncarnationApiView, MergeRequestStatus } from 'interfaces/incarnations.types'
import { JsonEditor } from 'components/common/JsonEditor/JsonEditor'
import { Tabs } from 'components/common/Tabs/Tabs'

const ErrorMessage = styled.div(({ theme }) => ({
  position: 'relative',
  color: theme.colors.contrastText,
  fontFamily: 'var(--monospace)',
  background: theme.colors.error,
  flex: 1,
  padding: 16,
  fontSize: 14,
  borderRadius: 4,
  lineHeight: 1.5,
  minHeight: 70,
  '.IconButton--Error': {
    color: theme.colors.contrastText,
    float: 'right'
  }
}))

const ErrorText = styled.div({
  paddingTop: 10
})

const DeleteIncarnationLink = styled.span`
  cursor: pointer;
  text-decoration: underline;
`

type FormProps = {
  mutation: (data: IncarnationInput) => Promise<IncarnationApiView>,
  deleteIncarnation?: () => Promise<void>,
  defaultValues: IncarnationInput,
  isEdit?: boolean,
  incarnationMergeRequestStatus?: MergeRequestStatus | null,
  mergeRequestUrl?: string | null,
  commitUrl?: string
  templateDataFull?: Record<string, never>
}

export const IncarnationsForm = ({
  mutation,
  defaultValues,
  isEdit,
  deleteIncarnation = () => Promise.resolve(),
  incarnationMergeRequestStatus,
  mergeRequestUrl,
  commitUrl,
  templateDataFull
}: FormProps) => {
  const { register, handleSubmit, formState: { errors }, control, getValues, watch } = useForm({
    defaultValues
  })
  const templateRepo = watch('templateRepository')
  const failed = templateRepo === '' && isEdit
  const [apiError, setApiError] = useState<ApiErrorResponse | null>()
  const navigate = useNavigate()
  const onBackClick = () => {
    const values = getValues()
    const formIsChanged = !isEqual(values, defaultValues)
    if (formIsChanged) {
      if (window.confirm('You have unsaved data. Are you sure you want to leave?')) {
        navigate('/incarnations')
      }
    } else {
      navigate('/incarnations')
    }
  }

  const queryClient = useQueryClient()
  const { mutateAsync, isLoading } = useMutation(mutation)
  const deleteMutation = useMutation(deleteIncarnation)
  const onDelete = async () => {
    if (window.confirm('Are you sure you want to delete this incarnation?')) {
      try {
        await deleteMutation.mutateAsync()
        await delay(1000)
        queryClient.invalidateQueries(['incarnations'])
        navigate('/incarnations')
      } catch (error) {
        setApiError(error as ApiErrorResponse)
      }
    }
  }

  const onSubmit: SubmitHandler<IncarnationInput> = async incarnation => {
    setApiError(null)
    try {
      console.log(incarnation)
      await mutateAsync(incarnation)
      await delay(1000)
      queryClient.invalidateQueries(['incarnations'])
    } catch (err) {
      const error = err as ApiErrorResponse
      setApiError(error)
    }
  }
  const title = <h3>{isEdit ? 'Edit' : 'Create'} incarnation</h3>
  const buttonTitle = isEdit
    ? isLoading ? 'Updating' : 'Update'
    : isLoading ? 'Creating' : 'Create'

  const deleteButtonTitle = deleteMutation.isSuccess ? 'Deleted!' : deleteMutation.isLoading ? 'Deleting' : 'Delete'
  const editTemplateDataController = <Controller
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
        height="max(calc(100vh - 700px), 200px)" />
    )} />
  const form = <Hug as="form" mb={16} flex mx={-8} onSubmit={handleSubmit(onSubmit)}>
    <Hug w="60%" miw={600} px={8}>
      <Hug mb={16}>
        <TextField autoFocus label="Incarnation repository" disabled={isLoading || isEdit} size="large" hasError={!!errors.repository} required {...register('repository', { required: true })} />
      </Hug>
      <Hug mb={16}>
        <TextField label="Target directory" size="large" disabled={isLoading || isEdit} hasError={!!errors.targetDirectory} {...register('targetDirectory')} />
      </Hug>
      <Hug mb={16} flex={['aic']}>
        <Hug w="100%">
          <TextField label="Template repository" disabled={isLoading || isEdit} size="large" hasError={!!errors.templateRepository} required {...register('templateRepository', { required: true })} />
        </Hug>
        {isUrl(templateRepo) && (
          <Hug ml={8}>
            <Tooltip title="Open in new tab">
              <a style={{ display: 'block' }} href={templateRepo} target="_blank" rel="noreferrer">
                <IconButton type="button"><OpenInNew /></IconButton>
              </a>
            </Tooltip>
          </Hug>
        )}
      </Hug>
      <Hug mb={16}>
        <TextField label="Template version" disabled={isLoading} size="large" hasError={!!errors.templateVersion} required {...register('templateVersion', { required: true })} />
      </Hug>
      {isEdit && (
        <Hug mb={16}>
          <Controller
            control={control}
            name="automerge"
            render={({ field: { onChange, value } }) => (
              <ToggleSwitch checked={value} label="Automerge" disabled={isLoading} onChange={e => onChange(e.target.checked)} />
            )} />
        </Hug>
      )}
      <Hug my={16}>
        {isEdit ? (
          <Tabs
            tabs={[
              {
                label: <strong>Template data JSON</strong>,
                content: <Hug my={8}>
                  {editTemplateDataController}
                </Hug>
              },
              {
                label: <strong>Full template data (readonly)</strong>,
                content: <Hug my={8}>
                  <JsonEditor
                    defaultValue={JSON.stringify(templateDataFull, null, 2)}
                    readOnly
                    height="max(calc(100vh - 700px), 200px)" />
                </Hug>
              }
            ]} />
        )
          : (
            <>
              <h4>Template data JSON</h4>
              <Hug my={16}>
                {editTemplateDataController}
              </Hug>
            </>
          )}
      </Hug>
      <Hug flex={['jcfe', 'aic']}>
        <Hug>
          <Button loading={isLoading} style={{ minWidth: 120 }} type="submit" disabled={isLoading}>{buttonTitle}</Button>
        </Hug>
      </Hug>
    </Hug>
    {apiError
      ? (
        <Hug w="40%" px={8}>
          <ErrorMessage>
            <IconButton flying onClick={() => setApiError(null)} className="IconButton--Error" >
              <Close />
            </IconButton>
            <ErrorText>{apiError.message}</ErrorText>
            <Hug>
              {apiError.documentation ? <a href={apiError.documentation} target="_blank" rel="noreferrer">Read more</a> : null}
            </Hug>
          </ErrorMessage>
        </Hug>
      )
      : null}
  </Hug>
  const failedFeedback = (
    <Hug as="form" mb={16} flex mx={-8}>
      <Hug w="60%" miw={600} px={8} pt={32}>
        It looks like this incarnation is not available anymore 😔.
        You can <DeleteIncarnationLink onClick={onDelete}>delete</DeleteIncarnationLink> it.
      </Hug>
    </Hug>
  )
  return (
    <Section>
      <Hug flex={['aic']} ml={-42} w="calc(60% + 42px)">
        <Hug mr={8}>
          <IconButton flying onClick={onBackClick}>
            <ExpandLeft />
          </IconButton>
        </Hug>
        <Hug flex={['aic']} w="100%" pr={6}>
          {title}
          {incarnationMergeRequestStatus && (
            <Hug ml={16}>
              <Tooltip title="Merge request status">
                <StatusTag
                  mergeRequestStatus={incarnationMergeRequestStatus ?? null} />
              </Tooltip>
            </Hug>
          )}
          {isEdit && (
            <Hug ml="auto" flex={['aic']}>
              <IncarnationLinks mergeRequestUrl={mergeRequestUrl} commitUrl={commitUrl} size="large" />
              <Hug ml={4}>
                <Tooltip title="Delete incarnation">
                  <Button
                    variant="danger"
                    disabled={deleteMutation.isLoading || deleteMutation.isSuccess}
                    loading={deleteMutation.isLoading}
                    onClick={onDelete}>{deleteButtonTitle}</Button>
                </Tooltip>
              </Hug>
            </Hug>
          )}
        </Hug>
      </Hug>
      {failed ? failedFeedback : form}

    </Section>
  )
}
