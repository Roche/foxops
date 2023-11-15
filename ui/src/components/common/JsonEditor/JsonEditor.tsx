import { useRef, useState, useEffect } from 'react'
import * as monaco from 'monaco-editor/esm/vs/editor/editor.api'
import styled from '@emotion/styled'
import { useThemeModeStore } from 'stores/theme-mode'
import { InputError } from '../InputError/InputError'

export interface JsonEditorProps {
  defaultValue?: string
  height?: number | string
  onChange?: (value: string) => void
  invalid?: boolean
  error?: string
  readOnly?: boolean
}

export const JsonEditor = ({
  defaultValue,
  height = 300,
  onChange = () => {},
  invalid,
  error,
  readOnly
}: JsonEditorProps) => {
  const [editor, setEditor] = useState<monaco.editor.IStandaloneCodeEditor | null>(null)
  const { mode } = useThemeModeStore()
  const monacoEl = useRef(null)

  useEffect(() => {
    if (monacoEl) {
      setEditor(editor => {
        if (editor) return editor
        const _editor = monaco.editor.create(monacoEl.current!, {
          value: defaultValue,
          language: 'json',
          automaticLayout: true,
          theme: mode === 'dark' ? 'vs-dark' : 'vs',
          fontSize: 14,
          readOnly,
          minimap: {
            enabled: false
          }
        })
        _editor.onDidChangeModelContent(() => {
          onChange(_editor.getValue())
        })
        return _editor
      })
    }

    return () => editor?.dispose()
  }, [monacoEl.current, readOnly])

  useEffect(() => {
    monaco.editor.setTheme(mode === 'dark' ? 'vs-dark' : 'vs')
  }, [mode])

  return (
    <>
      <EditorWrapper ref={monacoEl} style={{ height }} invalid={invalid} />
      {error ? <InputError>{error}</InputError> : null}
    </>
  )
}

const EditorWrapper = styled.div<{ invalid?: boolean }>(({ theme, invalid }) => ({
  '.monaco-editor': {
    border: `1px solid ${invalid ? theme.colors.error : theme.colors.inputBorder}`,
    borderRadius: 4,
    overflow: 'hidden'
  }
}))
