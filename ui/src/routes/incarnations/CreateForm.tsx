import { IncarnationInput, incarnations } from '../../services/incarnations'
import { IncarnationsForm } from './Form'

const defaultValues = {
  automerge: true,
  autoUpdateIntervalSeconds: 0,
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
