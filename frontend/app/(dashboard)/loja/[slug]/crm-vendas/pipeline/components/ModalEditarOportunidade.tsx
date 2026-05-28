'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { X, Mail, MessageCircle } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { normalizeListResponse, getCrmApiErrorDetail, crmMensagemEnvioCanalSucesso } from '@/lib/crm-utils';
import { crmEnviarCliente } from '@/lib/crm-enviar-cliente';
import type { Oportunidade } from '@/components/crm-vendas/PipelineBoard';
import ProdutoSeletorCategoria from '@/components/crm-vendas/ProdutoSeletorCategoria';

interface ProdutoServicoOption {
  id: number;
  nome: string;
  tipo: string;
  preco: string;
  codigo?: string;
  categoria_nome?: string;
}

interface Props {
  oportunidade: Oportunidade;
  onClose: () => void;
  onSuccess: () => void;
  slug: string;
  etapas: { key: string; label: string }[];
}

export default function ModalEditarOportunidade({ oportunidade, onClose, onSuccess, slug, etapas }: Props) {
  const [etapaSelecionada, setEtapaSelecionada] = useState(oportunidade.etapa);
  const [valorComissaoEdit, setValorComissaoEdit] = useState(oportunidade.valor_comissao || '');
  const [dataFechamentoGanho, setDataFechamentoGanho] = useState(oportunidade.data_fechamento_ganho || '');
  const [dataFechamentoPerdido, setDataFechamentoPerdido] = useState(oportunidade.data_fechamento_perdido || '');
  const [itensEditar, setItensEditar] = useState<{ id?: number; produto_servico_id: number; quantidade: string; preco_unitario: string }[]>([]);
  const [produtosServicos, setProdutosServicos] = useState<ProdutoServicoOption[]>([]);
  const [propostasOportunidade, setPropostasOportunidade] = useState<{ id: number; titulo: string }[]>([]);
  const [contratoOportunidade, setContratoOportunidade] = useState<{ id: number; titulo: string } | null>(null);
  const [modalExcluir, setModalExcluir] = useState(false);
  const [seletorEditarAberto, setSeletorEditarAberto] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [enviandoEnvio, setEnviandoEnvio] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);

  // Carregar itens e produtos ao montar
  useEffect(() => {
    apiClient
      .get(`/crm-vendas/oportunidade-itens/?oportunidade_id=${oportunidade.id}`)
      .then((res) => {
        const itens = normalizeListResponse(res.data);
        setItensEditar(itens.map((item: any) => ({
          id: item.id,
          produto_servico_id: item.produto_servico,
          quantidade: String(item.quantidade),
          preco_unitario: String(item.preco_unitario),
        })));
      })
      .catch(() => setItensEditar([]));

    apiClient
      .get<ProdutoServicoOption[] | { results: ProdutoServicoOption[] }>('/crm-vendas/produtos-servicos/?ativo=true')
      .then((res) => setProdutosServicos(normalizeListResponse(res.data)))
      .catch(() => setProdutosServicos([]));
  }, [oportunidade.id]);

  // Carregar propostas e contratos quando closed_won
  useEffect(() => {
    const isClosedWon = oportunidade.etapa === 'closed_won' || etapaSelecionada === 'closed_won';
    if (!isClosedWon) return;
    apiClient
      .get<{ results: { id: number; titulo: string }[] }>(`/crm-vendas/propostas/?oportunidade_id=${oportunidade.id}`)
      .then((r) => setPropostasOportunidade(normalizeListResponse(r.data)))
      .catch(() => setPropostasOportunidade([]));
    apiClient
      .get<{ results: { id: number; titulo: string }[] }>(`/crm-vendas/contratos/?oportunidade_id=${oportunidade.id}`)
      .then((r) => {
        const list = normalizeListResponse(r.data);
        setContratoOportunidade(list.length > 0 ? list[0] : null);
      })
      .catch(() => setContratoOportunidade(null));
  }, [oportunidade.id, oportunidade.etapa, etapaSelecionada]);

  const updateItemEditar = (idx: number, field: 'produto_servico_id' | 'quantidade' | 'preco_unitario', value: string | number) => {
    setItensEditar((itens) =>
      itens.map((item, i) => {
        if (i !== idx) return item;
        const updated = { ...item, [field]: field === 'produto_servico_id' ? Number(value) : String(value) };
        if (field === 'produto_servico_id') {
          const ps = produtosServicos.find((p) => p.id === Number(value));
          if (ps) updated.preco_unitario = ps.preco;
        }
        return updated;
      })
    );
  };

  const removeItemEditar = (idx: number) => {
    setItensEditar((itens) => itens.filter((_, i) => i !== idx));
  };

  const handleEnviarCliente = async (tipo: 'proposta' | 'contrato', id: number, canal: 'email' | 'whatsapp') => {
    setEnviandoEnvio(true);
    try {
      await crmEnviarCliente(tipo === 'proposta' ? 'propostas' : 'contratos', id, canal);
      alert(crmMensagemEnvioCanalSucesso(canal));
    } catch (err: unknown) {
      alert(getCrmApiErrorDetail(err, 'Erro ao enviar.'));
    } finally {
      setEnviandoEnvio(false);
    }
  };

  const handleExcluirOportunidade = async () => {
    setEnviando(true);
    try {
      await apiClient.delete(`/crm-vendas/oportunidades/${oportunidade.id}/`);
      onClose();
      onSuccess();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setFormErro(e.response?.data?.detail || 'Erro ao excluir oportunidade.');
    } finally {
      setEnviando(false);
    }
  };

  const handleSalvarEtapa = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormErro(null);
    setEnviando(true);
    
    try {
      const payload: Record<string, unknown> = { etapa: etapaSelecionada };
      
      // Adiciona valor_comissao se preenchido
      if (valorComissaoEdit) {
        payload.valor_comissao = parseFloat(valorComissaoEdit);
      }
      
      // Se mudou para closed_won, sugere data_fechamento_ganho
      if (etapaSelecionada === 'closed_won' && !dataFechamentoGanho) {
        payload.data_fechamento_ganho = new Date().toISOString().split('T')[0];
      } else if (dataFechamentoGanho) {
        payload.data_fechamento_ganho = dataFechamentoGanho;
      }
      
      // Se mudou para closed_lost, sugere data_fechamento_perdido
      if (etapaSelecionada === 'closed_lost' && !dataFechamentoPerdido) {
        payload.data_fechamento_perdido = new Date().toISOString().split('T')[0];
      } else if (dataFechamentoPerdido) {
        payload.data_fechamento_perdido = dataFechamentoPerdido;
      }

      // Atualizar oportunidade
      await apiClient.patch(`/crm-vendas/oportunidades/${oportunidade.id}/`, payload);
      
      // Atualizar itens (produtos/serviços)
      // Buscar itens atuais do backend
      const resItens = await apiClient.get(`/crm-vendas/oportunidade-itens/?oportunidade_id=${oportunidade.id}`);
      const itensAtuais = normalizeListResponse(resItens.data);
      const idsAtuais = itensAtuais.map((item: any) => item.id);
      const idsEditados = itensEditar.filter(item => item.id).map(item => item.id);
      
      // Deletar itens removidos
      for (const id of idsAtuais) {
        if (!idsEditados.includes(id)) {
          await apiClient.delete(`/crm-vendas/oportunidade-itens/${id}/`);
        }
      }
      
      // Atualizar ou criar itens
      for (const item of itensEditar) {
        const itemData = {
          oportunidade: oportunidade.id,
          produto_servico: item.produto_servico_id,
          quantidade: parseFloat(item.quantidade),
          preco_unitario: parseFloat(item.preco_unitario),
        };
        
        if (item.id) {
          // Atualizar item existente
          await apiClient.patch(`/crm-vendas/oportunidade-itens/${item.id}/`, itemData);
        } else {
          // Criar novo item
          await apiClient.post('/crm-vendas/oportunidade-itens/', itemData);
        }
      }
      
      // Recalcular valor total da oportunidade
      if (itensEditar.length > 0) {
        const valorTotal = itensEditar.reduce(
          (sum, item) => sum + parseFloat(item.quantidade) * parseFloat(item.preco_unitario),
          0
        );
        await apiClient.patch(`/crm-vendas/oportunidades/${oportunidade.id}/`, {
          valor: valorTotal,
        });
      }
      
      onClose();
      onSuccess();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setFormErro(e.response?.data?.detail || 'Erro ao atualizar.');
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
      onClick={() => !enviando && onClose()}
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-4xl max-h-[95vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Editar oportunidade
          </h2>
          <button
            type="button"
            onClick={() => !enviando && onClose()}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>
        <div className="p-4 flex-shrink-0">
          <p className="font-medium text-gray-900 dark:text-white">{oportunidade.titulo}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">{oportunidade.lead_nome}</p>
          <p className="text-sm font-semibold text-green-600 dark:text-green-400 mt-1">
            {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(parseFloat(String(oportunidade.valor)))}
          </p>
          {oportunidade.valor_comissao && (
            <p className="text-sm text-purple-600 dark:text-purple-400 mt-1">
              Comissão: {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(parseFloat(String(oportunidade.valor_comissao)))}
            </p>
          )}
        </div>
        <form id="form-editar-oportunidade" onSubmit={handleSalvarEtapa} className="overflow-y-auto flex-1">
          <div className="p-4 pt-0 space-y-4">
          {formErro && (
            <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg">
              {formErro}
            </p>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Etapa (mudar para &quot;Fechado ganho&quot; = registrar venda)
            </label>
            <select
              value={etapaSelecionada}
              onChange={(e) => setEtapaSelecionada(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              {etapas.map((o) => (
                <option key={o.key} value={o.key}>{o.label}</option>
              ))}
            </select>
          </div>
          
          {/* Produtos e Serviços */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Produtos e Serviços
              </label>
              <Link href={`/loja/${slug}/crm-vendas/produtos-servicos`} className="text-xs text-[#0176d3] hover:underline">
                Cadastrar
              </Link>
            </div>
            {itensEditar.map((item, idx) => {
              const ps = produtosServicos.find(p => p.id === item.produto_servico_id);
              return (
                <div key={idx} className="flex gap-2 mb-2 items-center bg-gray-50 dark:bg-gray-700/50 rounded-lg px-2 py-1.5">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
                      {ps?.codigo ? <span className="text-gray-400">[{ps.codigo}] </span> : null}
                      {ps?.nome || 'Produto'}
                    </p>
                    {ps?.categoria_nome && (
                      <p className="text-[10px] text-gray-500">{ps.categoria_nome}</p>
                    )}
                  </div>
                  <input
                    type="number" min="0.01" step="0.01"
                    value={item.preco_unitario}
                    onChange={(e) => updateItemEditar(idx, 'preco_unitario', e.target.value)}
                    className="w-20 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700"
                    placeholder="Preço"
                  />
                  <input
                    type="number" min="0.01" step="0.01"
                    value={item.quantidade}
                    onChange={(e) => updateItemEditar(idx, 'quantidade', e.target.value)}
                    className="w-14 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700"
                    placeholder="Qtd"
                  />
                  <button type="button" onClick={() => removeItemEditar(idx)} className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-500">
                    <X size={13} />
                  </button>
                </div>
              );
            })}
            {seletorEditarAberto && produtosServicos.length > 0 && (
              <div className="mb-2">
                <ProdutoSeletorCategoria
                  produtos={produtosServicos}
                  itensSelecionados={itensEditar.map(i => i.produto_servico_id)}
                  onSelecionar={(ps) => {
                    setItensEditar(itens => [...itens, { produto_servico_id: ps.id, quantidade: '1', preco_unitario: ps.preco }]);
                  }}
                  onFechar={() => setSeletorEditarAberto(false)}
                />
              </div>
            )}
            {produtosServicos.length > 0 && !seletorEditarAberto && (
              <button type="button" onClick={() => setSeletorEditarAberto(true)} className="text-sm text-[#0176d3] hover:underline">
                + Adicionar item
              </button>
            )}
            {produtosServicos.length === 0 && (
              <p className="text-xs text-amber-600 dark:text-amber-400">
                Cadastre produtos/serviços em <Link href={`/loja/${slug}/crm-vendas/produtos-servicos`} className="underline">Produtos e Serviços</Link>.
              </p>
            )}
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Valor da Comissão (R$)
            </label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={valorComissaoEdit}
              onChange={(e) => setValorComissaoEdit(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="0"
            />
          </div>
          {(etapaSelecionada === 'closed_won' || oportunidade.data_fechamento_ganho) && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Data Fechamento Ganho
              </label>
              <input
                type="date"
                value={dataFechamentoGanho}
                onChange={(e) => setDataFechamentoGanho(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
          )}
          {(etapaSelecionada === 'closed_lost' || oportunidade.data_fechamento_perdido) && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Data Fechamento Perdido
              </label>
              <input
                type="date"
                value={dataFechamentoPerdido}
                onChange={(e) => setDataFechamentoPerdido(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
          )}
          {(etapaSelecionada === 'closed_won' || oportunidade.etapa === 'closed_won') && (
            <div className="border-t border-gray-200 dark:border-gray-600 pt-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Enviar ao cliente
              </label>
              {(propostasOportunidade.length > 0 || contratoOportunidade) ? (
                <div className="space-y-2">
                  {propostasOportunidade.map((p) => (
                    <div key={p.id} className="flex items-center justify-between gap-2 p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <span className="text-sm truncate">Proposta: {p.titulo || `#${p.id}`}</span>
                      <div className="flex gap-1 shrink-0">
                        <button
                          type="button"
                          onClick={() => handleEnviarCliente('proposta', p.id, 'email')}
                          disabled={enviandoEnvio}
                          className="p-1.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50 disabled:opacity-50"
                          title="Enviar por e-mail"
                        >
                          <Mail size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleEnviarCliente('proposta', p.id, 'whatsapp')}
                          disabled={enviandoEnvio}
                          className="p-1.5 rounded bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-900/50 disabled:opacity-50"
                          title="Enviar por WhatsApp"
                        >
                          <MessageCircle size={16} />
                        </button>
                      </div>
                    </div>
                  ))}
                  {contratoOportunidade && (
                    <div className="flex items-center justify-between gap-2 p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <span className="text-sm truncate">Contrato: {contratoOportunidade.titulo || `#${contratoOportunidade.id}`}</span>
                      <div className="flex gap-1 shrink-0">
                        <button
                          type="button"
                          onClick={() => handleEnviarCliente('contrato', contratoOportunidade.id, 'email')}
                          disabled={enviandoEnvio}
                          className="p-1.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50 disabled:opacity-50"
                          title="Enviar por e-mail"
                        >
                          <Mail size={16} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleEnviarCliente('contrato', contratoOportunidade.id, 'whatsapp')}
                          disabled={enviandoEnvio}
                          className="p-1.5 rounded bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-900/50 disabled:opacity-50"
                          title="Enviar por WhatsApp"
                        >
                          <MessageCircle size={16} />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Crie uma proposta ou contrato em{' '}
                  <Link href={`/loja/${slug}/crm-vendas/propostas`} className="text-[#0176d3] hover:underline">Propostas</Link>
                  {' ou '}
                  <Link href={`/loja/${slug}/crm-vendas/contratos`} className="text-[#0176d3] hover:underline">Contratos</Link>
                  {' para enviar ao cliente.'}
                </p>
              )}
            </div>
          )}
          </div>
        </form>
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
          {!modalExcluir ? (
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => !enviando && onClose()}
                className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={() => setModalExcluir(true)}
                disabled={enviando}
                className="px-4 py-2 rounded-lg border border-red-300 dark:border-red-600 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50"
              >
                Excluir
              </button>
              <button
                type="submit"
                form="form-editar-oportunidade"
                disabled={enviando}
                className="flex-1 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium"
              >
                {enviando ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Tem certeza que deseja excluir a oportunidade &quot;{oportunidade.titulo}&quot;? Esta ação não pode ser desfeita.
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setModalExcluir(false)}
                  disabled={enviando}
                  className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={handleExcluirOportunidade}
                  disabled={enviando}
                  className="flex-1 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-medium"
                >
                  {enviando ? 'Excluindo...' : 'Confirmar exclusão'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
