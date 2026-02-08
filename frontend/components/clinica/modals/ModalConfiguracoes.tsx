'use client';
import { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import apiClient from '@/lib/api-client';
import { extractArrayData, formatApiError } from '@/lib/api-helpers';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

interface ModalConfiguracoesProps {
  loja: LojaInfo;
  onClose: () => void;
}

export default function ModalConfiguracoes({ loja, onClose }: ModalConfiguracoesProps) {
  const [activeTab, setActiveTab] = useState<'historico' | 'estatisticas' | 'geral'>('historico');
  const [loading, setLoading] = useState(true);
  const [historico, setHistorico] = useState<any[]>([]);
  const [estatisticas, setEstatisticas] = useState<any>(null);

  useEffect(() => {
    if (activeTab === 'historico') carregarHistorico();
    else if (activeTab === 'estatisticas') carregarEstatisticas();
  }, [activeTab]);

  const carregarHistorico = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/clinica/historico-acessos/');
      setHistorico(extractArrayData(response));
    } catch (error) {
      console.error('Erro:', error);
      setHistorico([]);
    } finally {
      setLoading(false);
    }
  };

  const carregarEstatisticas = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/clinica/historico-acessos/estatisticas/');
      setEstatisticas(response.data);
    } catch (error) {
      console.error('Erro:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={true} onClose={onClose} maxWidth="5xl">
      <div className="p-6">
        <h2 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>
          ⚙️ Configurações
        </h2>

        <div className="flex border-b mb-6">
          {[
            { id: 'historico', label: 'Histórico', icon: '📊' },
            { id: 'estatisticas', label: 'Estatísticas', icon: '📈' },
            { id: 'geral', label: 'Geral', icon: '⚙️' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-6 py-3 font-medium ${activeTab === tab.id ? 'border-b-2' : 'text-gray-500'}`}
              style={activeTab === tab.id ? { borderColor: loja.cor_primaria, color: loja.cor_primaria } : {}}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>

        {activeTab === 'historico' && (
          <div>
            {loading ? (
              <div className="text-center py-8">Carregando...</div>
            ) : historico.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-lg">Nenhum registro encontrado</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[60vh] overflow-y-auto">
                {historico.map((reg: any) => (
                  <div key={reg.id} className="flex gap-4 p-4 border rounded-xl">
                    <div className="flex-1">
                      <div className="flex gap-2 mb-1">
                        <p className="font-semibold">{reg.usuario_nome}</p>
                        <span className="px-2 py-0.5 text-xs rounded-full bg-blue-100">{reg.acao_display}</span>
                        {reg.recurso && <span className="px-2 py-0.5 text-xs rounded-full bg-purple-100">{reg.recurso}</span>}
                      </div>
                      <p className="text-sm text-gray-600">{reg.ip_address} • {reg.navegador}</p>
                      <p className="text-xs text-gray-500">{reg.data_hora}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'estatisticas' && (
          <div>
            {loading ? (
              <div className="text-center py-8">Carregando...</div>
            ) : !estatisticas ? (
              <div className="text-center py-12">Sem dados</div>
            ) : (
              <div className="space-y-6">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 border">
                  <div className="text-sm text-gray-500">Total de Ações</div>
                  <div className="text-3xl font-bold" style={{ color: loja.cor_primaria }}>
                    {estatisticas.total_acoes}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'geral' && (
          <div className="text-center py-12">
            <p>Em desenvolvimento</p>
          </div>
        )}

        <div className="flex justify-end pt-4 border-t mt-6">
          <button onClick={onClose} className="px-6 py-2 border rounded-lg hover:bg-gray-50">
            Fechar
          </button>
        </div>
      </div>
    </Modal>
  );
}
