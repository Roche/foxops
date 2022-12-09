import { useForm, SubmitHandler, useFieldArray } from 'react-hook-form'
import isEqual from 'lodash.isequal'
import { useNavigate } from 'react-router-dom'
import { Button } from '../../components/common/Button/Button'
import { Hug } from '../../components/common/Hug/Hug'
import { IconButton } from '../../components/common/IconButton/IconButton'
import { ExpandLeft } from '../../components/common/Icons/ExpandLeft'
import { Trash } from '../../components/common/Icons/Trash'
import { TextField } from '../../components/common/TextField/TextField'
import { Section, StatusTag } from './parts'
import { IncarnationApiView, IncarnationInput, IncarnationStatus } from '../../services/incarnations'
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

const ErrorMessage = styled.div(({ theme }) => ({
  position: 'relative',
  color: theme.colors.textContrast,
  fontFamily: 'var(--monospace)',
  background: theme.colors.error,
  flex: 1,
  padding: 16,
  fontSize: 14,
  borderRadius: 4,
  lineHeight: 1.5,
  minHeight: 70,
  '.IconButton--Error': {
    color: theme.colors.textContrast,
    float: 'right'
  }
}))

const ErrorText = styled.div({
  paddingTop: 10
})

type FormProps = {
  mutation: (data: IncarnationInput) => Promise<IncarnationApiView>,
  deleteIncarnation?: () => Promise<void>,
  defaultValues: IncarnationInput,
  isEdit?: boolean,
  incarnationStatus?: IncarnationStatus,
  mergeRequestUrl?: string | null,
  commitUrl?: string
}

export const IncarnationsForm = ({
  mutation,
  defaultValues,
  isEdit,
  deleteIncarnation = () => Promise.resolve(),
  incarnationStatus,
  mergeRequestUrl,
  commitUrl
}: FormProps) => {
  const { register, handleSubmit, formState: { errors }, control, getValues, setFocus, watch } = useForm({
    defaultValues
  })
  const [apiError, setApiError] = useState<ApiErrorResponse | null>()
  const { fields, append, remove } = useFieldArray({ name: 'templateData', control })
  const appendAndFocus = (key: string, value: string) => {
    append({ key, value })
    requestAnimationFrame(() => {
      if (key) {
        setFocus(`templateData.${fields.length}.key`)
      } else {
        setFocus(`templateData.${fields.length}.value`)
      }
    })
  }
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
  const { mutateAsync, isLoading, isSuccess } = useMutation(mutation)
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
      await mutateAsync(incarnation)
      await delay(1000)
      queryClient.invalidateQueries(['incarnations'])
      navigate('/incarnations')
    } catch (err) {
      const error = err as ApiErrorResponse
      setApiError(error)
    }
  }
  const title = <h3>{isEdit ? 'Edit' : 'Create'} incarnation</h3>
  const buttonTitle = isEdit
    ? isSuccess ? 'Updated!' : isLoading ? 'Updating' : 'Update'
    : isSuccess ? 'Created!' : isLoading ? 'Creating' : 'Create'

  const deleteButtonTitle = deleteMutation.isSuccess ? 'Deleted!' : deleteMutation.isLoading ? 'Deleting' : 'Delete'
  const templateRepo = watch('templateRepository')
  return (
    <Section>
      <Hug flex={['aic']} ml={-42} w="calc(60% + 42px)">
        <Hug mr={8}>
          <IconButton flying title="Back to incarnations" onClick={onBackClick}>
            <ExpandLeft />
          </IconButton>
        </Hug>
        <Hug flex={['aic']} w="100%" pr={6}>
          {title}
          {incarnationStatus && <Hug ml={16}><Tooltip title="Incarnation status"><StatusTag status={incarnationStatus} /></Tooltip></Hug>}
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
      <Hug as="form" mb={16} flex mx={-8} onSubmit={handleSubmit(onSubmit)}>
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
          <h4>Template data</h4>
          <Hug mb={16}>
            {fields.map((field, index) => (
              <Hug flex mb={8} mx={-4} key={field.id}>
                <Hug w="50%" px={4}>
                  <TextField disabled={isLoading} placeholder="Key" {...register(`templateData.${index}.key` as const)} />
                </Hug>
                <Hug w="50%" pl={4} pr={8}>
                  <TextField disabled={isLoading} placeholder="Value" {...register(`templateData.${index}.value` as const)} />
                </Hug>
                <Hug pr={4}>
                  <IconButton disabled={isLoading} type="button" onClick={() => remove(index)} title="Delete">
                    <Trash />
                  </IconButton>
                </Hug>
              </Hug>
            ))}
          </Hug>
          <Hug flex mb={8} ml={-8}>
            <Hug w="calc(50% - 18px)" pl={8} pr={4}>
              <TextField disabled={isLoading} placeholder="Start typing to add new key..." value="" onChange={e => {
                appendAndFocus(e.target.value, '')
              }} />
            </Hug>
            <Hug w="calc(50% + 18px)" pl={4}>
              <TextField disabled={isLoading} placeholder="...value pair" value="" onChange={e => {
                appendAndFocus('', e.target.value)
              }} />
            </Hug>
          </Hug>
          <Hug flex={['jcfe', 'aic']}>
            <Hug>
              <Button loading={isLoading} style={{ minWidth: 120 }} type="submit" disabled={isLoading || isSuccess}>{buttonTitle}</Button>
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
    </Section>
  )
}
