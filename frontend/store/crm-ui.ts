import { create } from 'zustand';

interface CRMUIState {
  collapsed: boolean;
  toggle: () => void;
}

// ✅ FIX: collapsed deve começar como true no mobile (menu fechado por padrão)
export const useCRMUIStore = create<CRMUIState>((set) => ({
  collapsed: true,
  toggle: () => set((s) => ({ collapsed: !s.collapsed })),
}));
