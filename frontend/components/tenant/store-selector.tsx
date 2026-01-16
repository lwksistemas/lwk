'use client';

import { useTenant } from '@/hooks/use-tenant';
import { authService } from '@/lib/auth';
import { useRouter } from 'next/navigation';

export function StoreSelector() {
  const { currentStore, stores, switchStore } = useTenant();
  const router = useRouter();

  const handleLogout = () => {
    authService.logout();
    router.push('/login');
  };

  return (
    <div className="flex items-center gap-4">
      {stores.length > 0 && (
        <select
          value={currentStore?.id || ''}
          onChange={(e) => switchStore(Number(e.target.value))}
          className="px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todas as lojas</option>
          {stores.map((store) => (
            <option key={store.id} value={store.id}>
              {store.name}
            </option>
          ))}
        </select>
      )}
      <button
        onClick={handleLogout}
        className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
      >
        Sair
      </button>
    </div>
  );
}
