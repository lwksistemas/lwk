import { useEffect } from 'react';
import { useTenantStore } from '@/lib/tenant';
import apiClient from '@/lib/api-client';

export function useTenant() {
  const { currentStore, stores, setCurrentStore, setStores } = useTenantStore();

  useEffect(() => {
    if (stores.length === 0) {
      loadStores();
    }
  }, []);

  const loadStores = async () => {
    try {
      const response = await apiClient.get('/stores/');
      setStores(response.data.results || response.data);
    } catch (error) {
      console.error('Erro ao carregar lojas:', error);
    }
  };

  const switchStore = (storeId: number) => {
    const store = stores.find((s) => s.id === storeId);
    if (store) {
      setCurrentStore(store);
    }
  };

  return {
    currentStore,
    stores,
    switchStore,
    loadStores,
  };
}
