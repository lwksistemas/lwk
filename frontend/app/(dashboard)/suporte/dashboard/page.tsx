'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import BotaoSuporte from '@/components/suporte/BotaoSuporte';
import { CardEstatisticas, TabelaChamados, ModalAtendimento } from '@/components/suporte/dashboard';

interface Resposta {
  id: number;
  usuario_nome: string;
  mensagem: string;
  is_suporte: boolean;
  created_at: string;
}

interface Chamado {
  id: number;
  titulo: string;
  descricao: string;
  tipo: string;
  loja_nome: string;
  loja_slug: string;
  usuario_nome: string;
  usuario_email: string;
  status: string;
  prioridade: string;
  respostas?: Resposta[];
  created_at: string;
  updated_at: string;
}

export default function SuporteDashboardPage() {
  const router = useRouter();
  const [chamados, setChamados] = useState<Chamado[]>([]);
  const [loading, setLoading] = useState(true);
  const [chamadoSelecionado, setChamadoSelecionado] = useState<Chamado | null>(null);
  const [modalAberto, setModalAberto] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const userType = authService.getUserType();
      if (userType !== 'suporte') {
        router.push('/suporte/login');
        return;
      }
      loadChamados();
    }
  }, [router]);

  const loadChamados = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/suporte/chamados/');
      setChamados(response.data.results || response.data);
    } catch (error) {
      console.error('Erro ao carregar chamados:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    authService.logout();
    router.push('/suporte/login');
  };

  const handleAtender = (chamado: Chamado) => {
    // Recarregar o chamado completo com respostas
    apiClient.get(`/suporte/chamados/${chamado.id}/`)
      .then(response => {
        setChamadoSelecionado(response.data);
        setModalAberto(true);
      })
      .catch(error => {
        console.error('Erro ao carregar chamado:', error);
        // Fallback: usar dados da lista
        setChamadoSelecionado(chamado);
        setModalAberto(true);
      });
  };

  const handleIniciarAtendimento = async (chamadoId: number) => {
    try {
      await apiClient.patch(`/suporte/chamados/${chamadoId}/`, {
        status: 'em_andamento'
      });
      loadChamados();
      alert('Atendimento iniciado!');
    } catch (error) {
      console.error('Erro ao iniciar atendimento:', error);
      alert('Erro ao iniciar atendimento');
    }
  };

  const handleResolver = async (chamadoId: number) => {
    if (!confirm('Deseja marcar este chamado como resolvido?')) return;
    
    try {
      await apiClient.post(`/suporte/chamados/${chamadoId}/resolver/`);
      loadChamados();
      setModalAberto(false);
      alert('Chamado marcado como resolvido!');
    } catch (error) {
      console.error('Erro ao resolver chamado:', error);
      alert('Erro ao resolver chamado');
    }
  };

  const handleEnviarResposta = async (chamadoId: number, mensagem: string) => {
    try {
      await apiClient.post(`/suporte/chamados/${chamadoId}/responder/`, {
        mensagem
      });
      
      // Recarregar o chamado completo para atualizar as respostas
      const response = await apiClient.get(`/suporte/chamados/${chamadoId}/`);
      setChamadoSelecionado(response.data);
      
      // Atualizar lista de chamados
      loadChamados();
      
      alert('Resposta enviada com sucesso!');
    } catch (error) {
      console.error('Erro ao enviar resposta:', error);
      alert('Erro ao enviar resposta');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-blue-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div>
              <h1 className="text-2xl font-bold">Portal de Suporte</h1>
              <p className="text-blue-200 text-sm">Gerenciamento de Chamados</p>
            </div>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-md transition-colors"
            >
              Sair
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Estatísticas */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <CardEstatisticas 
              titulo="Total de Chamados" 
              valor={chamados.length} 
              cor="blue" 
            />
            <CardEstatisticas 
              titulo="Abertos" 
              valor={chamados.filter(c => c.status === 'aberto').length} 
              cor="yellow" 
            />
            <CardEstatisticas 
              titulo="Em Andamento" 
              valor={chamados.filter(c => c.status === 'em_andamento').length} 
              cor="blue" 
            />
            <CardEstatisticas 
              titulo="Resolvidos" 
              valor={chamados.filter(c => c.status === 'resolvido').length} 
              cor="green" 
            />
          </div>

          {/* Chamados */}
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b">
              <h3 className="text-lg font-semibold">Chamados</h3>
            </div>
            <div className="p-6">
              <TabelaChamados 
                chamados={chamados}
                loading={loading}
                onAtender={handleAtender}
              />
            </div>
          </div>
        </div>
      </main>
      
      {/* Modal de Atendimento */}
      <ModalAtendimento
        chamado={chamadoSelecionado}
        isOpen={modalAberto}
        onClose={() => setModalAberto(false)}
        onIniciarAtendimento={handleIniciarAtendimento}
        onResolver={handleResolver}
        onEnviarResposta={handleEnviarResposta}
      />
      
      {/* Botão Flutuante de Suporte */}
      <BotaoSuporte />
    </div>
  );
}
