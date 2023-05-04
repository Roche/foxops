import create from 'zustand'

interface CanShowVersionStore {
  canShow: boolean,
  setCanShow: (canShow: boolean) => void
}

export const useCanShowStatusStore = create<CanShowVersionStore>()(set => ({
  canShow: false,
  setCanShow: (canShow: boolean) => set(() => ({ canShow }))
}))
