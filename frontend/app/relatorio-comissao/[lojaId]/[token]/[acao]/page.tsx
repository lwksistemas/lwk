'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { CheckCircle, FileText, AlertTriangle } from 'lucide-react';
import { getPrimaryApiBaseUrl } from '@/lib/api-base';

interface RelatorioData {
  numero: string;
  titulo: string;
  status: string;
  empresa: string;
  vendedor?: string;
  periodo: string;
  valor_total_vendas?: string;
  valor_total_comissao: string;
  quantidade_vendas?: number;
  pode_aprovar?: boolean;
  pode_reprovar?: boolean;
  pode_assinar?: boolean;
  empresa_aprovado_em?: string;
}

export default function RelatorioComissaoPublicPage() {
  const params = useParams();
  const lojaId = params.lojaId as string;
  const token = params.token as string;
  const acao = params.acao as string; // 'aprovar' | 'reprovar' | 'assinar'

  const [dados, setDados] = useState<RelatorioData | null>(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');
  const [sucesso, setSucesso] = useState(false);
  const [processando, setProcessando] = useState(false);
  const [nome, setNome] = useState('');
  const [motivo, setMotivo] = useState('');

  const endpoint = acao === 'assinar'
    ? `/crm-vendas/relatorio-comissao/${lojaId}/${token}/assinar/`
    : acao === 'reprovar'
      ? `/crm-vendas/relatorio-comissao/${lojaId}/${token}/reprovar/`
      : `/crm-vendas/relatorio-comissao/${lojaId}/${token}/aprovar/`;

  useEffect(() => {
    (async () => {
      try {
        const url = getPrimaryApiBaseUrl();
        const res = await fetch(`${url}${endpoint}`);
        const data = await res.json();
        if (!res.ok) { setErro(data.detail || 'Link inválido.'); return; }
        setDados(data);
        setNome(data.empresa || data.vendedor || '');
      } catch { setErro('Erro ao carregar dados.'); }
      finally { setLoading(false); }
    })();
  }, [endpoint]);

  const handleSubmit = async () => {
    if (acao === 'reprovar' && !motivo.trim()) {
      setErro('Informe o motivo da reprovação.');
      return;
    }
    setProcessando(true);
    setErro('');
    try {
      const url = getPrimaryApiBaseUrl();
      const body: Record<string, string> = {};
      if (acao === 'reprovar') body.motivo = motivo;
      else body.nome = nome;

      const res = await fetch(`${url}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) { setErro(data.detail || 'Erro ao processar.'); return; }
      setSucesso(true);
    } catch { setErro('Erro de conexão.'); }
    finally { setProcessando(false); }
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <p className="text-gray-500">Carregando...</p>
    </div>
  );

  if (erro && !dados) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-xl shadow-lg max-w-md text-center">
        <AlertTriangle className="mx-auto text-red-500 mb-4" size={48} />
        <p className="text-red-600 font-medium">{erro}</p>
      </div>
    </div>
  );

  if (sucesso) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-xl shadow-lg max-w-md text-center">
        <CheckCircle className="mx-auto text-green-500 mb-4" size={48} />
        <h2 className="text-xl font-bold text-gray-900 mb-2">
          {acao === 'aprovar' ? 'Relatório Aprovado!' : acao === 'reprovar' ? 'Relatório Reprovado' : 'Assinatura Registrada!'}
        </h2>
        <p className="text-gray-600">
          {acao === 'aprovar' && 'O vendedor será notificado para assinar.'}
          {acao === 'reprovar' && 'O prestador será notificado sobre a divergência.'}
          {acao === 'assinar' && 'O boleto será gerado e enviado para pagamento.'}
        </p>
      </div>
    </div>
  );

  const titulo = acao === 'aprovar' ? 'Aprovar Relatório' : acao === 'reprovar' ? 'Reprovar Relatório' : 'Assinar Relatório';
  const corHeader = acao === 'reprovar' ? 'from-red-500 to-red-700' : 'from-blue-600 to-indigo-700';

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-lg mx-auto">
        {/* Header */}
        <div className={`bg-gradient-to-r ${corHeader} rounded-t-2xl p-6 text-center text-white`}>
          <FileText className="mx-auto mb-2" size={32} />
          <h1 className="text-xl font-bold">{titulo}</h1>
          <p className="text-sm opacity-90 mt-1">Relatório {dados?.numero}</p>
        </div>

        {/* Body */}
        <div className="bg-white rounded-b-2xl shadow-lg p-6 space-y-4">
          {/* Info do relatório */}
          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Empresa:</span>
              <span className="font-medium">{dados?.empresa}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Período:</span>
              <span className="font-medium">{dados?.periodo}</span>
            </div>
            {dados?.quantidade_vendas !== undefined && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Vendas:</span>
                <span className="font-medium">{dados.quantidade_vendas}</span>
              </div>
            )}
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Comissão:</span>
              <span className="font-bold text-green-700">
                R$ {parseFloat(dados?.valor_total_comissao || '0').toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </span>
            </div>
          </div>

          {erro && <p className="text-red-600 text-sm bg-red-50 p-2 rounded">{erro}</p>}

          {/* Form */}
          {acao === 'reprovar' ? (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Motivo da reprovação *</label>
              <textarea value={motivo} onChange={e => setMotivo(e.target.value)} rows={3} placeholder="Descreva o motivo..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Seu nome</label>
              <input type="text" value={nome} onChange={e => setNome(e.target.value)} placeholder="Nome completo"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
          )}

          {/* Botão */}
          <button onClick={handleSubmit} disabled={processando}
            className={`w-full py-3 rounded-lg font-semibold text-white transition disabled:opacity-50 ${
              acao === 'reprovar' ? 'bg-red-600 hover:bg-red-700' : 'bg-blue-600 hover:bg-blue-700'
            }`}>
            {processando ? 'Processando...' : acao === 'aprovar' ? '✓ Aprovar Relatório' : acao === 'reprovar' ? '✗ Reprovar' : '✍️ Assinar'}
          </button>

          <p className="text-xs text-gray-500 text-center">
            {acao !== 'reprovar' && 'Ao confirmar, seu IP e data/hora serão registrados.'}
          </p>
        </div>
      </div>
    </div>
  );
}
