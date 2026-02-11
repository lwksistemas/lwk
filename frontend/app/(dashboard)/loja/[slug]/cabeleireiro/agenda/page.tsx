'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { authService } from '@/lib/auth';
import apiClient from '@/lib/api-client';
import CalendarioCabeleireiro from '@/components/cabeleireiro/CalendarioCabeleireiro';
import { ModalAgendamentos } from '@/components/cabeleireiro/modals';
import { ArrowLeft } from 'lucide-react';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
}

export default function AgendaCabeleireiroPage() {
  const router = useRouter();
  const params = useParams();
  const slug = params.slug as string;
  
  const [lojaInfo, setLojaInfo] = useState<LojaInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [modalAberto, setModalAberto] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const userType = authService.getUserType();
      if (userType !== 'loja') {
        router.push(`/loja/${slug}/login`);
        return;
      }

      carregarLoja();
    }
  }, [router, slug]);

  const carregarLoja = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
      const data = response.data;
      
      if (data?.id && typeof window !== 'undefined') {
        sessionStorage.setItem('current_loja_id', String(data.id));
        if (data.slug) sessionStorage.setItem('loja_slug', data.slug);
      }
      
      setLojaInfo(data);
    } catch (error: any) {
      console.error('Erro ao carregar loja:', error);
      if (error.response?.status === 401) {
        router.push(`/loja/${slug}/login`);
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Carregando agenda...</p>
        </div>
      </div>
    );
  }

  if (!lojaInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            Erro ao carregar loja
          </h2>
          <button
            onClick={() => router.push(`/loja/${slug}/dashboard`)}
            className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            Voltar ao Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-purple-50 dark:from-gray-900 dark:to-gray-800">
      {/* Header */}
      <div 
        className="text-white shadow-lg"
        style={{ backgroundColor: lojaInfo.cor_primaria }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push(`/loja/${slug}/dashboard`)}
                className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-xl font-bold">{lojaInfo.nome}</h1>
                <p className="text-sm opacity-90">Agenda de Agendamentos</p>
              </div>
            </div>
            <button
              onClick={() => {
                const html = document.documentElement;
                const isDark = html.classList.contains('dark');
                if (isDark) {
                  html.classList.remove('dark');
                  localStorage.setItem('theme', 'light');
                } else {
                  html.classList.add('dark');
                  localStorage.setItem('theme', 'dark');
                }
              }}
              className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
            >
              Tema
            </button>
          </div>
        </div>
      </div>

      {/* Conteúdo */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <CalendarioCabeleireiro 
          loja={lojaInfo} 
          onNovoAgendamento={() => setModalAberto(true)}
        />
      </div>

      {/* Modal de Novo Agendamento */}
      {modalAberto && (
        <ModalAgendamentos 
          loja={lojaInfo} 
          onClose={() => setModalAberto(false)} 
        />
      )}
    </div>
  );
}
