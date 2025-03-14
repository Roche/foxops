import { api } from './api'

export const template = {
  getDefaultVariables: async (templateRepository: string, templateVersion: string) => {
    const data = await api.get<undefined, Record<string, string>>(`/templates/variables?template_repository=${templateRepository}&template_version=${templateVersion}`)
    return data
  }
}

