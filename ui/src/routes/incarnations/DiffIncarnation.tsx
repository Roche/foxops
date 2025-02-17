import { useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { Diff2HtmlUI } from 'diff2html/lib/ui/js/diff2html-ui-slim.js'
import 'diff2html/bundles/css/diff2html.min.css'
import { IconButton } from 'components/common/IconButton/IconButton'
import { ExpandLeft } from 'components/common/Icons/ExpandLeft'
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
  const {
    isError: isErrorIncarnation,
    data: incarnationData,
    isSuccess: isSuccessIncarnation
  } = useQuery(['incarnations', Number(id)], () => incarnations.getById(id))
  const { isLoading, isError, data, isSuccess } = useQuery(
    ['incarnation_diff', Number(id)],
    () => incarnations.getDiffToTemplate(id)
  )

  function onBackClick() {
    window.location.href = '/incarnations/' + id
  }

  const pendingMessage = isLoading
    ? 'Loading...'
    : isError || isErrorIncarnation
      ? 'Error loading incarnation diff 😔'
      : null

  const { setCanShow } = useCanShowStatusStore()

  useEffect(() => {
    if (!isSuccess) return
    setCanShow(true)
  }, [isSuccess, setCanShow])

  if (isSuccess && diffInjectorRef.current) {
    const d2h = new Diff2HtmlUI(diffInjectorRef.current, data, {
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

    if (/https?:\/\//.test(incarnationData?.commitUrl || '')) {
      const incarnationBaseUrl = incarnationData?.commitUrl.match(/(.*?)(?:\/-)?\/commit/)?.[1]

      diffInjectorRef.current
        .querySelectorAll('.d2h-file-name')
        .forEach((el: Element) => {
          const sibling = el.nextElementSibling

          if (sibling?.classList.contains('d2h-deleted')) {
            return // It is not possible to display a link to a deleted file on the incarnation
          }

          el.classList.add('diff-file-link')

          el = el as HTMLElement

          el.addEventListener('click', () => {
            window.open(`${incarnationBaseUrl}/blob/${incarnationData?.commitSha}/${el.innerHTML.substring(23)}`, '_blank')
          })
        })
    }
  }

  return isSuccess && isSuccessIncarnation ? (
    <Section>
      <Hug mr={8} mb={16} ml={-42} flex={['aic']} w="100%">
        <IconButton flying onClick={onBackClick}>
          <ExpandLeft />
        </IconButton>
        <h3>Diff view to template</h3>
      </Hug>
      <Hug mb={16}>
        {isSuccess && !data ? (
          <strong>There are no manual changes to the template</strong>
        ) : (
          <span>
            The following diff shows all the changes, which where manually made
            to the incernation. Those changes are not tracked by foxops and will
            not be rendered if the incarnation is recreated.
          </span>
        )}
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
