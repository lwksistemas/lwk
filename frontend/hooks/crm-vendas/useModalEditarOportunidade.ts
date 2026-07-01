'use client';

import { useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import { normalizeListResponse, getCrmApiErrorDetail, crmMensagemEnvioCanalSucesso } from '@/lib/crm-utils';
import { crmEnviarCliente } from '@/lib/crm-enviar-cliente';
import { useToast } from '@/components/ui/Toast';
import { useWhatsappEnvioFlags } from '@/hooks/useWhatsappEnvioFlags';
import type { Oportunidade } from '@/components/crm-vendas/PipelineBoard';
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

interface OportunidadeItemApi {
  id: number;
  produto_servico: number;
  quantidade: number;
  preco_unitario: number;
}

export function useModalEditarOportunidade(
  oportunidade: Oportunidade,
  onClose: () => void,
  onSuccess: () => void,
) {
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
    oportunidade.empresa_prestadora ? String(oportunidade.empresa_prestadora) : '',
  );
  const [prestadoras, setPrestadoras] = useState<ContaPrestadoraOption[]>([]);
  const { proposta: propostaWhatsappHabilitada, contrato: contratoWhatsappHabilitado } = useWhatsappEnvioFlags();

  useEffect(() => {
    apiClient
      .get(`/crm-vendas/oportunidade-itens/?oportunidade_id=${oportunidade.id}`)
      .then((res) => {
        const itens = normalizeListResponse<OportunidadeItemApi>(res.data);
        setItensEditar(
          itens.map((item) => ({
            id: item.id,
            produto_servico_id: item.produto_servico,
            quantidade: String(item.quantidade),
            preco_unitario: String(item.preco_unitario),
          })),
        );
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

  const updateItemEditar = (
    idx: number,
    field: 'produto_servico_id' | 'quantidade' | 'preco_unitario',
    value: string | number,
  ) => {
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
      toast.success('Oportunidade excluída.');
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

      if (valorComissaoEdit) {
        payload.valor_comissao = parseFloat(valorComissaoEdit);
      }

      if (etapaSelecionada === 'closed_won' && !dataFechamentoGanho) {
        payload.data_fechamento_ganho = new Date().toISOString().split('T')[0];
      } else if (dataFechamentoGanho) {
        payload.data_fechamento_ganho = dataFechamentoGanho;
      }

      if (etapaSelecionada === 'closed_lost' && !dataFechamentoPerdido) {
        payload.data_fechamento_perdido = new Date().toISOString().split('T')[0];
      } else if (dataFechamentoPerdido) {
        payload.data_fechamento_perdido = dataFechamentoPerdido;
      }

      await apiClient.patch(`/crm-vendas/oportunidades/${oportunidade.id}/`, payload);

      const resItens = await apiClient.get(`/crm-vendas/oportunidade-itens/?oportunidade_id=${oportunidade.id}`);
      const itensAtuais = normalizeListResponse<OportunidadeItemApi>(resItens.data);
      const idsAtuais = itensAtuais.map((item) => item.id);
      const idsEditados = itensEditar.filter((item) => item.id).map((item) => item.id);

      for (const id of idsAtuais) {
        if (!idsEditados.includes(id)) {
          await apiClient.delete(`/crm-vendas/oportunidade-itens/${id}/`);
        }
      }

      for (const item of itensEditar) {
        const itemData = {
          oportunidade: oportunidade.id,
          produto_servico: item.produto_servico_id,
          quantidade: parseFloat(item.quantidade),
          preco_unitario: parseFloat(item.preco_unitario),
        };

        if (item.id) {
          await apiClient.patch(`/crm-vendas/oportunidade-itens/${item.id}/`, itemData);
        } else {
          await apiClient.post('/crm-vendas/oportunidade-itens/', itemData);
        }
      }

      if (itensEditar.length > 0) {
        const valorTotal = calcularTotalOportunidadeItens(itensEditar);
        await apiClient.patch(`/crm-vendas/oportunidades/${oportunidade.id}/`, {
          valor: valorTotal,
        });
      }

      onClose();
      onSuccess();
      toast.success('Oportunidade atualizada.');
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setFormErro(e.response?.data?.detail || 'Erro ao atualizar.');
    } finally {
      setEnviando(false);
    }
  };

  return {
    etapaSelecionada,
    setEtapaSelecionada,
    valorComissaoEdit,
    setValorComissaoEdit,
    dataFechamentoGanho,
    setDataFechamentoGanho,
    dataFechamentoPerdido,
    setDataFechamentoPerdido,
    itensEditar,
    setItensEditar,
    produtosServicos,
    propostasOportunidade,
    contratoOportunidade,
    modalExcluir,
    setModalExcluir,
    seletorEditarAberto,
    setSeletorEditarAberto,
    enviando,
    enviandoEnvio,
    formErro,
    empresaPrestadoraId,
    setEmpresaPrestadoraId,
    prestadoras,
    propostaWhatsappHabilitada,
    contratoWhatsappHabilitado,
    updateItemEditar,
    removeItemEditar,
    handleEnviarCliente,
    handleExcluirOportunidade,
    handleSalvarEtapa,
  };
}
