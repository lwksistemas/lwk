import { create } from 'zustand';

export interface Store {
  id: number;
  name: string;
  slug: string;
  description: string;
  logo: string;
  is_active: boolean;
}

interface TenantState {
  currentStore: Store | null;
  stores: Store[];
  setCurrentStore: (store: Store | null) => void;
  setStores: (stores: Store[]) => void;
  clearTenant: () => void;
}

export const useTenantStore = create<TenantState>()((set) => ({
  currentStore: null,
  stores: [],
  setCurrentStore: (store) => set({ currentStore: store }),
  setStores: (stores) => set({ stores }),
  clearTenant: () => set({ currentStore: null, stores: [] }),
}));
