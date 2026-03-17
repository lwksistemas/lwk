'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import apiClient from '@/lib/api-client';
import { ArrowLeft } from 'lucide-react';
import PropostaFormContent from '@/components/crm-vendas/PropostaFormContent';
import type { LojaInfo, LeadInfo } from '@/components/crm-vendas/modals/ModalPropostaForm';

interface OportunidadeOption {
  id: number;
  titulo: string;
  lead: number;
  lead_nome: string;
  valor: string;
  etapa: string;
}

interface OportunidadeItem {
  id: number;
  produto_servico: number;
  produto_servico_nome: string;
  produto_servico_tipo: string;
  quantidade: string;
  preco_unitario: string;
  subtotal: number;
  observacao?: string;
}

const STATUS_LABEL: Record<string, string> = {
  rascunho: 'Rascunho',
  enviada: 'Enviada',
  aceita: 'Aceita',
  rejeitada: 'Rejeitada',
};

function normalizeList<T>(data: T[] | { results: T[] }): T[] {
  return Array.isArray(data) ? data : (data?.results ?? []);
}

export default function NovaPropostaPage() {
  const params = useParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const [formData, setFormData] = useState({
    oportunidade_id: '',
    titulo: '',
    conteudo: '',
    valor_total: '',
    status: 'rascunho' as string,
  });
  const [oportunidades, setOportunidades] = useState<OportunidadeOption[]>([]);
  const [itensOportunidade, setItensOportunidade] = useState<OportunidadeItem[]>([]);
  const [lojaInfo, setLojaInfo] = useState<LojaInfo | null>(null);
  const [leadInfo, setLeadInfo] = useState<LeadInfo | null>(null);
  const [propostaConteudoPadrao, setPropostaConteudoPadrao] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [salvandoPadrao, setSalvandoPadrao] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);

  const loadOportunidades = useCallback(async () => {
    try {
      const res = await apiClient.get<OportunidadeOption[] | { results: OportunidadeOption[] }>(
        '/crm-vendas/oportunidades/'
      );
      setOportunidades(normalizeList(res.data));
    } catch {
      setOportunidades([]);
    }
  }, []);

  const loadItensOportunidade = useCallback(async (oportunidadeId: string) => {
    if (!oportunidadeId) {
      setItensOportunidade([]);
      return;
    }
    try {
      const res = await apiClient.get<OportunidadeItem[] | { results: OportunidadeItem[] }>(
        `/crm-vendas/oportunidade-itens/?oportunidade_id=${oportunidadeId}`
      );
      setItensOportunidade(normalizeList(res.data));
    } catch {
      setItensOportunidade([]);
    }
  }, []);

  const loadLojaInfo = useCallback(async () => {
    try {
      const res = await apiClient.get<LojaInfo>(`/superadmin/lojas/info_publica/?slug=${slug}`);
      setLojaInfo(res.data);
    } catch {
      setLojaInfo(null);
    }
  }, [slug]);

  const loadCrmConfig = useCallback(async () => {
    try {
      const res = await apiClient.get<{ proposta_conteudo_padrao?: string }>('/crm-vendas/config/');
      setPropostaConteudoPadrao(res.data?.proposta_conteudo_padrao ?? '');
    } catch {
      setPropostaConteudoPadrao('');
    }
  }, []);

  const loadLeadInfo = useCallback(async (leadId: number) => {
    if (!leadId) {
      setLeadInfo(null);
      return;
    }
    try {
      const res = await apiClient.get<LeadInfo>(`/crm-vendas/leads/${leadId}/`);
      setLeadInfo(res.data);
    } catch {
      setLeadInfo(null);
    }
  }, []);

  useEffect(() => {
    loadOportunidades();
    loadLojaInfo();
    loadCrmConfig();
  }, [loadOportunidades, loadLojaInfo, loadCrmConfig]);

  useEffect(() => {
    if (propostaConteudoPadrao && !formData.conteudo) {
      setFormData((f) => ({ ...f, conteudo: propostaConteudoPadrao }));
    }
  }, [propostaConteudoPadrao]);

  useEffect(() => {
    if (formData.oportunidade_id) {
      loadItensOportunidade(formData.oportunidade_id);
      const opp = oportunidades.find((o) => String(o.id) === formData.oportunidade_id);
      if (opp?.lead) {
        loadLeadInfo(opp.lead);
      } else {
        setLeadInfo(null);
      }
    } else {
      setItensOportunidade([]);
      setLeadInfo(null);
    }
  }, [formData.oportunidade_id, oportunidades, loadItensOportunidade, loadLeadInfo]);

  const handleOportunidadeChange = (id: string) => {
    const opp = oportunidades.find((o) => String(o.id) === id);
    setFormData((f) => ({
      ...f,
      oportunidade_id: id,
      valor_total: opp?.valor ? String(opp.valor) : f.valor_total,
    }));
    loadItensOportunidade(id);
    if (opp?.lead) {
      loadLeadInfo(opp.lead);
    } else {
      setLeadInfo(null);
    }
  };

  const handleSalvarComoPadrao = useCallback(async (conteudo: string) => {
    try {
      setSalvandoPadrao(true);
      await apiClient.patch('/crm-vendas/config/', { proposta_conteudo_padrao: conteudo });
      setPropostaConteudoPadrao(conteudo);
      alert('Proposta PADRAO salva com sucesso! O conteúdo será usado em novas propostas.');
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      alert(e.response?.data?.detail || 'Erro ao salvar.');
    } finally {
      setSalvandoPadrao(false);
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormErro(null);
    if (!formData.titulo.trim()) {
      setFormErro('Título é obrigatório');
      return;
    }
    if (!formData.oportunidade_id) {
      setFormErro('Selecione uma oportunidade');
      return;
    }
    try {
      setSubmitting(true);
      await apiClient.post('/crm-vendas/propostas/', {
        oportunidade: parseInt(formData.oportunidade_id, 10),
        titulo: formData.titulo.trim(),
        conteudo: formData.conteudo,
        valor_total: formData.valor_total ? parseFloat(formData.valor_total) : null,
        status: formData.status,
      });
      router.push(`/loja/${slug}/crm-vendas/propostas`);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setFormErro(e.response?.data?.detail || 'Erro ao salvar.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-full">
      <div className="flex items-center gap-4 mb-6">
        <Link
          href={`/loja/${slug}/crm-vendas/propostas`}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400"
          aria-label="Voltar"
        >
          <ArrowLeft size={20} />
        </Link>
        <div>
          <h1 className="text-2xl font-semibold text-gray-800 dark:text-white">Nova Proposta</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            Preencha os dados da proposta comercial
          </p>
        </div>
      </div>

      <div className="bg-white dark:bg-[#16325c] rounded-xl border border-gray-200 dark:border-[#0d1f3c] p-6 w-full">
          <PropostaFormContent
          form={formData}
          formErro={formErro}
          enviando={submitting}
          lojaInfo={lojaInfo}
          leadInfo={leadInfo}
          oportunidades={oportunidades}
          itensOportunidade={itensOportunidade}
          statusOpcoes={Object.entries(STATUS_LABEL).map(([value, label]) => ({ value, label }))}
          onFormChange={setFormData}
          onOportunidadeChange={handleOportunidadeChange}
          onSubmit={handleSubmit}
          isEdit={false}
          onSalvarComoPadrao={handleSalvarComoPadrao}
          salvandoPadrao={salvandoPadrao}
          showCancel={true}
          onCancel={() => router.push(`/loja/${slug}/crm-vendas/propostas`)}
          fullWidth
        />
      </div>
    </div>
  );
}
