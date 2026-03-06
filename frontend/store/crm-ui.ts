import { create } from 'zustand';

interface CRMUIState {
  collapsed: boolean;
  toggle: () => void;
}

export const useCRMUIStore = create<CRMUIState>((set) => ({
  collapsed: false,
  toggle: () => set((s) => ({ collapsed: !s.collapsed })),
}));
