import { useForm, SubmitHandler, useFieldArray } from 'react-hook-form'
import isEqual from 'lodash.isequal'
import { useNavigate } from 'react-router-dom'
import { Button } from '../../components/common/Button/Button'
import { Hug } from '../../components/common/Hug/Hug'
import { IconButton } from '../../components/common/IconButton/IconButton'
import { ExpandLeft } from '../../components/common/Icons/ExpandLeft'
import { Trash } from '../../components/common/Icons/Trash'
import { TextField } from '../../components/common/TextField/TextField'
import { Section } from './parts'
import { IncarnationInput, incarnations } from '../../services/incarnations'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ApiErrorResponse } from '../../services/api'
import { delay } from '../../utils'
import { useState } from 'react'
import styled from '@emotion/styled'
import { Close } from '../../components/common/Icons/Close'
import { useRequestProcessingStore } from '../../stores/request-processing-store'
import { Loader } from '../../components/common/Loader/Loader'

const defaultValues: IncarnationInput = {
  repository: '',
  targetDirectory: '',
  templateRepository: '',
  templateVersion: '',
  templateData: []
}

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
  '.IconButton--Error': {
    color: theme.colors.textContrast,
    float: 'right'
  }
}))

export const IncarnationsCreateForm = () => {
  const { register, handleSubmit, formState: { errors }, control, getValues, setFocus } = useForm<IncarnationInput>({
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
  const { mutateAsync, isLoading, isSuccess } = useMutation((incarnation: IncarnationInput) => incarnations.create(incarnation))
  const { setPending } = useRequestProcessingStore()
  const onSubmit: SubmitHandler<IncarnationInput> = async incarnation => {
    setApiError(null)
    setPending(true)
    try {
      await mutateAsync(incarnation)
      await delay(1000)
      queryClient.invalidateQueries(['incarnations'])
      navigate('/incarnations')
    } catch (err) {
      const error = err as ApiErrorResponse
      setApiError(error)
    } finally {
      setPending(false)
    }
  }
  const buttonTitle = isSuccess ? 'Created!' : isLoading ? 'Creating' : 'Create'
  return (
    <Section>
      <Hug flex={['aic']} ml={-42}>
        <Hug mr={8}>
          <IconButton flying title="Back to incarnations" onClick={onBackClick}>
            <ExpandLeft />
          </IconButton>
        </Hug>
        <Hug>
          <h3>Create incarnation</h3>
        </Hug>
      </Hug>
      <Hug as="form" mb={16} flex mx={-8} onSubmit={handleSubmit(onSubmit)}>
        <Hug w="60%" miw={600} px={8}>
          <Hug mb={16}>
            <TextField autoFocus label="Incarnation repository" disabled={isLoading} size="large" hasError={!!errors.repository} required {...register('repository', { required: true })} />
          </Hug>
          <Hug mb={16}>
            <TextField label="Target directory" size="large" disabled={isLoading} hasError={!!errors.targetDirectory} {...register('targetDirectory')} />
          </Hug>
          <Hug mb={16}>
            <TextField label="Template repository" disabled={isLoading} size="large" hasError={!!errors.templateRepository} required {...register('templateRepository', { required: true })} />
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
                {apiError.message}
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
