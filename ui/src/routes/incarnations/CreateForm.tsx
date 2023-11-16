import { IncarnationInput, incarnations } from '../../services/incarnations'
import { IncarnationsForm } from './Form'

const defaultValues = {
  automerge: true,
  repository: '',
  targetDirectory: '',
  templateRepository: '',
  templateVersion: '',
  templateData: '{}'
}

export const CreateIncarnationForm = () => (
  <IncarnationsForm
    mutation={(incarnation: IncarnationInput) => incarnations.create(incarnation)}
    defaultValues={defaultValues} />
)
