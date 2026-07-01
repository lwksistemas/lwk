'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { X } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { normalizeListResponse, getCrmApiErrorDetail, crmMensagemEnvioCanalSucesso, formatCrmBrl } from '@/lib/crm-utils';
import { crmEnviarCliente } from '@/lib/crm-enviar-cliente';
import { useToast } from '@/components/ui/Toast';
import { useWhatsappEnvioFlags } from '@/hooks/useWhatsappEnvioFlags';
import type { Oportunidade } from '@/components/crm-vendas/PipelineBoard';
import OportunidadeItensEditor from '@/components/crm-vendas/OportunidadeItensEditor';
import CrmEnviarClienteIcones from '@/components/crm-vendas/CrmEnviarClienteIcones';
import {
  atualizarOportunidadeItem,
  calcularTotalOportunidadeItens,
  type OportunidadeItemRow,
} from '@/lib/crm-oportunidade-itens-utils';

interface ProdutoServicoOption {
  id: number;
  nome: string;
  tipo: string;
  preco: string;
  codigo?: string;
  categoria_nome?: string;
}

interface ContaPrestadoraOption {
  id: number;
  nome: string;
}

interface Props {
  oportunidade: Oportunidade;
  onClose: () => void;
  onSuccess: () => void;
  slug: string;
  etapas: { key: string; label: string }[];
}

export default function ModalEditarOportunidade({ oportunidade, onClose, onSuccess, slug, etapas }: Props) {
  const toast = useToast();
  const [etapaSelecionada, setEtapaSelecionada] = useState(oportunidade.etapa);
  const [valorComissaoEdit, setValorComissaoEdit] = useState(oportunidade.valor_comissao || '');
  const [dataFechamentoGanho, setDataFechamentoGanho] = useState(oportunidade.data_fechamento_ganho || '');
  const [dataFechamentoPerdido, setDataFechamentoPerdido] = useState(oportunidade.data_fechamento_perdido || '');
  const [itensEditar, setItensEditar] = useState<OportunidadeItemRow[]>([]);
  const [produtosServicos, setProdutosServicos] = useState<ProdutoServicoOption[]>([]);
  const [propostasOportunidade, setPropostasOportunidade] = useState<{ id: number; titulo: string }[]>([]);
  const [contratoOportunidade, setContratoOportunidade] = useState<{ id: number; titulo: string } | null>(null);
  const [modalExcluir, setModalExcluir] = useState(false);
  const [seletorEditarAberto, setSeletorEditarAberto] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [enviandoEnvio, setEnviandoEnvio] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [empresaPrestadoraId, setEmpresaPrestadoraId] = useState(
    oportunidade.empresa_prestadora ? String(oportunidade.empresa_prestadora) : ''
  );
  const [prestadoras, setPrestadoras] = useState<ContaPrestadoraOption[]>([]);
  const { proposta: propostaWhatsappHabilitada, contrato: contratoWhatsappHabilitado } = useWhatsappEnvioFlags();

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

    apiClient
      .get<ContaPrestadoraOption[] | { results: ContaPrestadoraOption[] }>('/crm-vendas/contas/?tipo=prestadora')
      .then((res) => setPrestadoras(normalizeListResponse(res.data)))
      .catch(() => setPrestadoras([]));
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
    setItensEditar((itens) => atualizarOportunidadeItem(itens, idx, field, value, produtosServicos));
  };

  const removeItemEditar = (idx: number) => {
    setItensEditar((itens) => itens.filter((_, i) => i !== idx));
  };

  const handleEnviarCliente = async (tipo: 'proposta' | 'contrato', id: number, canal: 'email' | 'whatsapp') => {
    setEnviandoEnvio(true);
    try {
      const segment = tipo === 'proposta' ? 'propostas' : 'contratos';
      const msg = await crmEnviarCliente(segment, id, canal);
      toast.success(msg || crmMensagemEnvioCanalSucesso(canal));
    } catch (err: unknown) {
      toast.error(getCrmApiErrorDetail(err, 'Erro ao enviar.'));
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
      if (!empresaPrestadoraId) {
        setFormErro('Selecione a empresa prestadora.');
        setEnviando(false);
        return;
      }

      const payload: Record<string, unknown> = {
        etapa: etapaSelecionada,
        empresa_prestadora: parseInt(empresaPrestadoraId, 10),
      };
      
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
        const valorTotal = calcularTotalOportunidadeItens(itensEditar);
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
            {formatCrmBrl(oportunidade.valor)}
          </p>
          {oportunidade.valor_comissao && (
            <p className="text-sm text-purple-600 dark:text-purple-400 mt-1">
              Comissão: {formatCrmBrl(oportunidade.valor_comissao)}
            </p>
          )}
          {oportunidade.empresa_prestadora_nome && (
            <p className="text-sm text-indigo-600 dark:text-indigo-400 mt-1">
              Prestadora atual: {oportunidade.empresa_prestadora_nome}
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
              Empresa prestadora *
            </label>
            <select
              value={empresaPrestadoraId}
              onChange={(e) => setEmpresaPrestadoraId(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">Selecione...</option>
              {prestadoras.map((c) => (
                <option key={c.id} value={c.id}>{c.nome}</option>
              ))}
            </select>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Define em qual relatório de comissão esta venda aparece.
            </p>
          </div>
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
          <OportunidadeItensEditor
            slug={slug}
            produtos={produtosServicos}
            itens={itensEditar}
            seletorAberto={seletorEditarAberto}
            onSeletorAbertoChange={setSeletorEditarAberto}
            onUpdateItem={updateItemEditar}
            onRemoveItem={removeItemEditar}
            onAddProduto={(ps) => {
              setItensEditar((itens) => [
                ...itens,
                { produto_servico_id: ps.id, quantidade: '1', preco_unitario: ps.preco },
              ]);
            }}
            layout="modal"
          />
          
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
                      <CrmEnviarClienteIcones
                        variant="modal"
                        whatsappHabilitado={propostaWhatsappHabilitada}
                        enviando={enviandoEnvio}
                        onEnviar={(canal) => handleEnviarCliente('proposta', p.id, canal)}
                      />
                    </div>
                  ))}
                  {contratoOportunidade && (
                    <div className="flex items-center justify-between gap-2 p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <span className="text-sm truncate">Contrato: {contratoOportunidade.titulo || `#${contratoOportunidade.id}`}</span>
                      <CrmEnviarClienteIcones
                        variant="modal"
                        whatsappHabilitado={contratoWhatsappHabilitado}
                        enviando={enviandoEnvio}
                        onEnviar={(canal) => handleEnviarCliente('contrato', contratoOportunidade.id, canal)}
                      />
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
