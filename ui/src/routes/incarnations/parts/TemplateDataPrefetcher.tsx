import styled from '@emotion/styled'
import { Button } from 'components/common/Button/Button'
import { Hug } from 'components/common/Hug/Hug'
import { Tooltip } from 'components/common/Tooltip/Tooltip'
import { useState } from 'react'
import { template } from '../../../services/template'

type TemplateDataPrefetcherProps = {
    templateRepository: string,
    templateVersion: string,
    children: React.ReactNode,
    onFetchSuccess?: (data: Record<string, string>) => void
};

const PreFetchWrapper = styled.div(({
  height: '100%',
  position: 'relative'
}))

const PreFetchBoxWrapper = styled.div(({
  height: '100%',
  position: 'absolute',
  top: 0,
  left: 0,
  width: '100%',
  zIndex: 100,
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  backgroundColor: 'rgba(165, 165, 165, 0.6)'
}))

const PreFetchBox = styled.div(({
  backgroundColor: 'rgba(49, 49, 49, 0.6)',
  width: '80%',
  minHeight: '60%',
  maxHeight: '85%',
  padding: '1rem',
  borderRadius: '.8rem',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  color: 'white',
  boxShadow: '0 0 5px rgba(0, 0, 0, 0.2)'
}))

const TemplateDataPrefetcherTitle = styled.h1(({
  textAlign: 'center'
}))

const TemplateDataPrefetcherContent = styled.div(({
  padding: '.5rem',
  textAlign: 'center' }))

const TemplateDataPrefetcherActions = styled.div(({
  display: 'flex',
  justifyContent: 'center',
  padding: '.5rem'
}))

const MagicButton = styled.button(({
  position: 'absolute',
  bottom: '.8rem',
  right: '.8rem',
  width: '2.5rem',
  height: '2.5rem',
  fontSize: '1.5rem',
  borderRadius: '50%',
  border: '1px solid rgb(137, 137, 137)',
  cursor: 'pointer',
  padding: 0,
  paddingBottom: '.2rem',
  paddingLeft: '.2rem',
  backgroundColor: 'rgba(255, 255, 255, 0.15)',

  '&:hover': {
    backgroundColor: 'rgba(255, 255, 255, 0.2)'
  }

}))

export const TemplateDataPrefetcher = ({ templateRepository, templateVersion, children, onFetchSuccess }: TemplateDataPrefetcherProps) => {
  const [isActivated, setIsActivated] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const fetchData = async () => {
    if (onFetchSuccess) {
      setIsLoading(true)
      const data = await template.getDefaultVariables(templateRepository, templateVersion)
      setIsLoading(false)
      setIsActivated(false)
      onFetchSuccess(data)

      // TODO implement error handeling, if the fetch fails
    }
  }

  const missingFields = []
  if (!templateRepository) {
    missingFields.push('Template repository')
  }
  if (!templateVersion) {
    missingFields.push('Template version')
  }

  return isActivated ? (
    <PreFetchWrapper>
      <PreFetchBoxWrapper>
        <PreFetchBox>
          <TemplateDataPrefetcherTitle>Automatically populate the template data</TemplateDataPrefetcherTitle>
          <TemplateDataPrefetcherContent>
        You can automatically prefetch the data from the repository, which you have provided.
          </TemplateDataPrefetcherContent>
          <TemplateDataPrefetcherContent>
        If you would wish to do so, click the button &quot;Prefetch data&quot; below. This will populate the template data with the data found in the repository.
          </TemplateDataPrefetcherContent>
          <TemplateDataPrefetcherContent>
            <strong>Note: This will overwrite the current template data. And is not reversible.</strong>
          </TemplateDataPrefetcherContent>
          <TemplateDataPrefetcherActions style={{ height: '2rem' }}>
            {missingFields.length > 0 && (
              <span style={{ color: '#fc2121', margin: 0 }}>
                Please fill in the missing data: <strong>{missingFields.join(', ')}</strong>
              </span>
            )}
          </TemplateDataPrefetcherActions>

          <TemplateDataPrefetcherActions>
            <Hug m=".5rem">
              <Tooltip title="Fetch data">
                <Button loading={isLoading} minWidth="9.5rem" disabled={(!templateRepository || !templateVersion) || isLoading} type="button" onClick={fetchData}>Prefetch data</Button>
              </Tooltip>
            </Hug><Hug m=".5rem">
              <Button variant="warning" minWidth="9.5rem" type="button" disabled={isLoading} onClick={() => setIsActivated(false)}>Continue Editing</Button>
            </Hug>
          </TemplateDataPrefetcherActions>
        </PreFetchBox>
      </PreFetchBoxWrapper>
      {children}
    </PreFetchWrapper>) : (
    <PreFetchWrapper>
      {children}
      <MagicButton type="button" onClick={() => setIsActivated(true)}>🪄</MagicButton>
    </PreFetchWrapper>
  )
}
