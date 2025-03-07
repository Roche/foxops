import { useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { Diff2HtmlUI } from 'diff2html/lib/ui/js/diff2html-ui-slim.js'
import 'diff2html/bundles/css/diff2html.min.css'
import { Hug } from 'components/common/Hug/Hug'
import { useThemeModeStore } from 'stores/theme-mode'
import { ColorSchemeType } from 'diff2html/lib/types'
import { incarnations } from '../../services/incarnations'
import { useQuery } from '@tanstack/react-query'
import { useCanShowStatusStore } from 'stores/show-status'
import { Loader } from 'components/common/Loader/Loader'
import { Section } from './parts'

export const DiffIncarnation = () => {
  const diffInjectorRef = useRef<HTMLDivElement>(null)
  const { id } = useParams()
  const { mode } = useThemeModeStore()

  const { isLoading, isError, data: incarnationDiff, isSuccess } = useQuery(
    ['incarnation_diff', id],
    () => incarnations.getDiffToTemplate(id)
  )

  let pendingMessage = null

  if (isLoading) {
    pendingMessage = 'Loading...'
  } else if (isError) {
    pendingMessage = 'Error loading incarnation diff 😔'
  }

  const { setCanShow } = useCanShowStatusStore()

  useEffect(() => {
    if (!isSuccess) return
    setCanShow(true)
  }, [isSuccess, setCanShow])

  useEffect(() => {
    if (isSuccess && diffInjectorRef.current) {
      const d2h = new Diff2HtmlUI(diffInjectorRef.current, incarnationDiff, {
        drawFileList: false,
        matching: 'lines',
        synchronisedScroll: true,
        outputFormat: 'side-by-side',
        highlight: true,
        diffMaxChanges: 1000,
        colorScheme:
        mode === 'dark' ? ColorSchemeType.DARK : ColorSchemeType.LIGHT
      })

      d2h.draw()
    }
  }, [incarnationDiff, isSuccess, mode])

  return isSuccess ? (
    <Section>
      <Hug mb={16}>
        {isSuccess && !incarnationDiff && <strong>There are no manual changes to the template</strong>
        }
      </Hug>
      <Hug w="100%">
        <div ref={diffInjectorRef}></div>
      </Hug>
    </Section>
  ) : (
    <Hug flex pl={8}>
      <Hug mr={4}>{pendingMessage}</Hug>
      {isLoading && <Loader />}
    </Hug>
  )
}
