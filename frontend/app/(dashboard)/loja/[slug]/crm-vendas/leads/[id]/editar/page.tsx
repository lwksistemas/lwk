'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import { STATUS_LEAD_OPCOES } from '@/constants/crm';
import { formatCpfCnpj } from '@/lib/consulta-cnpj';
import { buildCrmLeadPayload } from '@/lib/crm-utils';
import { formatCep, formatTelefone } from '@/lib/format-br';
import { LeadCadastroForm } from '@/components/crm-vendas/LeadCadastroForm';
import { EMPTY_FORM_LEAD } from '@/lib/crm-lead-form-types';
import type { Lead } from '@/components/crm-vendas/LeadsTable';
import { useCrmCepCnpjLookup } from '@/hooks/crm-vendas/useCrmCepCnpjLookup';

export default function EditarLeadPage() {
  const params = useParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const id = parseInt(String(params?.id ?? ''), 10);
  const basePath = `/loja/${slug}/crm-vendas/leads`;
  const { origensAtivas } = useCRMConfig();

  const [form, setForm] = useState(EMPTY_FORM_LEAD);
  const [enviando, setEnviando] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const { handleBuscarCnpj, handleBuscarCep, buscarCepLoading, buscarCnpjLoading } =
    useCrmCepCnpjLookup<typeof form>((updater) => setForm(updater), { upperCaseEndereco: true });

  useEffect(() => {
    if (isNaN(id)) {
      router.replace(basePath);
      return;
    }
    let cancelled = false;
    apiClient
      .get<Lead>(`/crm-vendas/leads/${id}/`)
      .then((res) => {
        if (cancelled) return;
        const lead = res.data;
        setForm({
          nome: lead.nome,
          empresa: lead.empresa || '',
          cpf_cnpj: lead.cpf_cnpj || '',
          email: lead.email || '',
          telefone: formatTelefone(lead.telefone || ''),
          origem: lead.origem,
          status: lead.status,
          cep: lead.cep || '',
          logradouro: lead.logradouro || '',
          numero: lead.numero || '',
          complemento: lead.complemento || '',
          bairro: lead.bairro || '',
          cidade: lead.cidade || '',
          uf: lead.uf || '',
          observacoes: lead.observacoes || '',
        });
      })
      .catch(() => {
        if (!cancelled) router.replace(basePath);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [basePath, id, router]);

  const voltarLista = () => {
    router.push(basePath);
  };

  const handleCpfCnpjChange = (value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 14);
    const updates: Partial<typeof form> = { cpf_cnpj: formatCpfCnpj(digits) };
    if (digits.length === 11) {
      updates.empresa = '';
    }
    setForm((f) => ({ ...f, ...updates }));
  };

  const handleCepChange = (value: string) => {
    setForm((f) => ({ ...f, cep: formatCep(value) }));
  };

  const handleSave = () => {
    setFormErro(null);
    if (!form.nome.trim()) {
      setFormErro('Informe o nome.');
      return;
    }
    setEnviando(true);
    apiClient
      .patch(`/crm-vendas/leads/${id}/`, buildCrmLeadPayload(form))
      .then(() => {
        router.push(basePath);
      })
      .catch((err) => {
        setFormErro(
          err.response?.data?.nome?.[0] || err.response?.data?.detail || 'Erro ao salvar lead.',
        );
      })
      .finally(() => setEnviando(false));
  };

  if (loading) {
    return (
      <div className="-m-4 sm:-m-6 lg:-m-8 flex flex-1 items-center justify-center min-h-[calc(100dvh-3.5rem)] bg-[#f3f2f2] dark:bg-[#0d1f3c]">
        <p className="text-gray-500 dark:text-gray-400">Carregando...</p>
      </div>
    );
  }

  return (
    <div className="-m-4 sm:-m-6 lg:-m-8 flex flex-col min-h-[calc(100dvh-3.5rem)]">
      <LeadCadastroForm
        form={form}
        onFormChange={(updater) => setForm(updater)}
        error={formErro}
        saving={enviando}
        origensAtivas={origensAtivas}
        statusOpcoes={[...STATUS_LEAD_OPCOES]}
        buscarCepLoading={buscarCepLoading}
        buscarCnpjLoading={buscarCnpjLoading}
        onCepChange={handleCepChange}
        onBuscarCep={() => handleBuscarCep(form.cep)}
        onBuscarCnpj={() => handleBuscarCnpj(form.cpf_cnpj)}
        onCpfCnpjChange={handleCpfCnpjChange}
        onSave={handleSave}
        onCancel={voltarLista}
        editing
      />
    </div>
  );
}
