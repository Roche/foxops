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
import { useMutation } from '@tanstack/react-query'
// import { delay } from '../../utils'

const defaultValues: IncarnationInput = {
  repository: '',
  targetDirectory: '',
  templateRepository: '',
  templateVersion: '',
  templateData: []
}

export const IncarnationsCreateForm = () => {
  const { register, handleSubmit, formState: { errors }, control, getValues } = useForm<IncarnationInput>({
    defaultValues
  })
  const { fields, append, remove } = useFieldArray({ name: 'templateData', control })
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

  // const queryClient = useQueryClient()
  // const { mutateAsync, isLoading, isSuccess } = useMutation((incarnation: IncarnationInput) => new Promise(r => {
  //   setTimeout(r, 2000)
  // }))
  const { mutateAsync, isLoading, isSuccess, isError, data } = useMutation((incarnation: IncarnationInput) => incarnations.create(incarnation))
  const onSubmit: SubmitHandler<IncarnationInput> = async incarnation => {
    await mutateAsync(incarnation)
    console.log(isError, data)
    // await delay(1000)
    // queryClient.invalidateQueries(['incarnations'])
    // navigate('/incarnations')
  }
  const buttonTitle = isSuccess ? 'Created!' : isLoading ? 'Saving...' : 'Create'
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
            <TextField autoFocus label="Repository" size="large" hasError={!!errors.repository} required {...register('repository', { required: true })} />
          </Hug>
          <Hug mb={16}>
            <TextField label="Target directory" size="large" hasError={!!errors.targetDirectory} required {...register('targetDirectory', { required: true })} />
          </Hug>
          <Hug mb={16}>
            <TextField label="Template repository" size="large" hasError={!!errors.templateRepository} required {...register('templateRepository', { required: true })} />
          </Hug>
          <Hug mb={16}>
            <TextField label="Template version" size="large" hasError={!!errors.templateVersion} required {...register('templateVersion', { required: true })} />
          </Hug>
          <h4>Template data</h4>
          <Hug mb={16}>
            {fields.map((field, index) => (
              <Hug flex mb={8} mx={-4} key={field.id}>
                <Hug w="50%" px={4}>
                  <TextField placeholder="Key" {...register(`templateData.${index}.key` as const)} />
                </Hug>
                <Hug w="50%" pl={4} pr={8}>
                  <TextField placeholder="Value" {...register(`templateData.${index}.value` as const)} />
                </Hug>
                <IconButton type="button" onClick={() => remove(index)} title="Delete">
                  <Trash />
                </IconButton>
              </Hug>
            ))}
          </Hug>
          <Hug flex mb={8} mx={-8}>
            <Hug w="50%" px={8}>
              <TextField placeholder="Start typing to add new key value pair" value="" onChange={e => {
                append({ key: e.target.value, value: '' })
              }} />
            </Hug>
          </Hug>
          <Hug flex={['jcfe']}><Button style={{ width: 100 }} type="submit">{buttonTitle}</Button></Hug>
        </Hug>
      </Hug>
    </Section>
  )
}
