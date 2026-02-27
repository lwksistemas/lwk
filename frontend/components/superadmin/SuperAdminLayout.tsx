'use client';

import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';
import { ThemeToggle } from '@/components/ui/ThemeProvider';
import { ReactNode } from 'react';

interface SuperAdminLayoutProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
}

export default function SuperAdminLayout({ children, title, subtitle }: SuperAdminLayoutProps) {
  const router = useRouter();

  const handleLogout = () => {
    authService.logout();
    router.push('/superadmin/login');
  };

  const handleVoltar = () => {
    router.push('/superadmin/dashboard');
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <nav className="bg-purple-900 dark:bg-purple-950 text-white shadow-lg">
        <div className="w-full max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <button
                onClick={handleVoltar}
                className="text-purple-200 dark:text-purple-300 hover:text-white transition-colors"
                title="Voltar ao Dashboard"
              >
                ← Voltar
              </button>
              <div>
                <h1 className="text-xl font-bold">{title || 'Super Admin'}</h1>
                {subtitle && (
                  <span className="text-sm text-purple-200 dark:text-purple-300">{subtitle}</span>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {/* Botão de Dark Mode */}
              <ThemeToggle />
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-800 rounded-md transition-colors"
              >
                Sair
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="w-full max-w-full py-6 px-4 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  );
}
