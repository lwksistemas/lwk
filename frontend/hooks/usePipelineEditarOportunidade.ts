/**
 * Hook que encapsula a lógica de edição de oportunidade no Pipeline.
 * Extraído de pipeline/page.tsx para melhor organização.
 */
import { useState, useCallback, useEffect } from 'react';
import apiClient from '@/lib/api-client';
import { normalizeListResponse, getCrmApiErrorDetail } from '@/lib/crm-utils';
import type { Oportunidade } from '@/components/crm-vendas/PipelineBoard';

interface ProdutoServicoOption {
  id: number;
  nome: string;
  tipo: string;
  preco: string;
  codigo?: string;
  categoria_nome?: string;
}

export interface ItemEditar {
  id?: number;
  produto_servico_id: number;
  quantidade: string;
  preco_unitario: string;
}

export function usePipelineEditarOportunidade(onSucesso: () => void) {
  const [oportunidadeEditar, setOportunidadeEditar] = useState<Oportunidade | null>(null);
  const [etapaSelecionada, setEtapaSelecionada] = useState('');
  const [valorComissaoEdit, setValorComissaoEdit] = useState('');
  const [dataFechamentoGanho, setDataFechamentoGanho] = useState('');
  const [dataFechamentoPerdido, setDataFechamentoPerdido] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [itensEditar, setItensEditar] = useState<ItemEditar[]>([]);
  const [produtosServicos, setProdutosServicos] = useState<ProdutoServicoOption[]>([]);
  const [propostasOportunidade, setPropostasOportunidade] = useState<{ id: number; titulo: string }[]>([]);
  const [contratoOportunidade, setContratoOportunidade] = useState<{ id: number; titulo: string } | null>(null);
  const [modalExcluir, setModalExcluir] = useState(false);
  const [seletorEditarAberto, setSeletorEditarAberto] = useState(false);

  const abrirEditar = useCallback((op: Oportunidade) => {
    setOportunidadeEditar(op);
    setEtapaSelecionada(op.etapa);
    setValorComissaoEdit(op.valor_comissao || '');
    setDataFechamentoGanho(op.data_fechamento_ganho || '');
    setDataFechamentoPerdido(op.data_fechamento_perdido || '');
    setFormErro(null);
    setModalExcluir(false);
    setPropostasOportunidade([]);
    setContratoOportunidade(null);

    // Carregar itens
    apiClient
      .get(`/crm-vendas/oportunidade-itens/?oportunidade_id=${op.id}`)
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

    // Carregar produtos/serviços
    apiClient
      .get<ProdutoServicoOption[] | { results: ProdutoServicoOption[] }>('/crm-vendas/produtos-servicos/?ativo=true')
      .then((res) => setProdutosServicos(normalizeListResponse(res.data)))
      .catch(() => setProdutosServicos([]));
  }, []);

  const fecharEditar = useCallback(() => {
    setOportunidadeEditar(null);
  }, []);

  const adicionarItem = useCallback((produto: ProdutoServicoOption) => {
    setItensEditar((itens) => [
      ...itens,
      { produto_servico_id: produto.id, quantidade: '1', preco_unitario: produto.preco },
    ]);
  }, []);

  const atualizarItem = useCallback((idx: number, field: 'produto_servico_id' | 'quantidade' | 'preco_unitario', value: string | number) => {
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
  }, [produtosServicos]);

  const removerItem = useCallback((idx: number) => {
    setItensEditar((itens) => itens.filter((_, i) => i !== idx));
  }, []);

  return {
    oportunidadeEditar, setOportunidadeEditar,
    etapaSelecionada, setEtapaSelecionada,
    valorComissaoEdit, setValorComissaoEdit,
    dataFechamentoGanho, setDataFechamentoGanho,
    dataFechamentoPerdido, setDataFechamentoPerdido,
    enviando, setEnviando,
    formErro, setFormErro,
    itensEditar, setItensEditar,
    produtosServicos, setProdutosServicos,
    propostasOportunidade, setPropostasOportunidade,
    contratoOportunidade, setContratoOportunidade,
    modalExcluir, setModalExcluir,
    seletorEditarAberto, setSeletorEditarAberto,
    abrirEditar, fecharEditar,
    adicionarItem, atualizarItem, removerItem,
  };
}
