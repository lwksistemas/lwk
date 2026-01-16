'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const userType = authService.getUserType();
      
      // Redirecionar para o dashboard correto baseado no tipo de usuário
      if (userType === 'superadmin') {
        router.push('/superadmin/dashboard');
      } else if (userType === 'suporte') {
        router.push('/suporte/dashboard');
      } else if (userType === 'loja') {
        const lojaSlug = authService.getLojaSlug();
        if (lojaSlug) {
          router.push(`/loja/dashboard?slug=${lojaSlug}`);
        } else {
          router.push('/loja/login');
        }
      } else {
        // Não autenticado, redirecionar para login
        router.push('/superadmin/login');
      }
    }
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
        <p className="mt-4 text-gray-600">Redirecionando...</p>
      </div>
    </div>
  );
}
