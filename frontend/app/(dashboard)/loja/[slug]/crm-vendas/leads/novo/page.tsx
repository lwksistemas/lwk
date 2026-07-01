'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import { STATUS_LEAD_OPCOES } from '@/constants/crm';
import { formatCpfCnpj } from '@/lib/consulta-cnpj';
import { buildCrmLeadPayload } from '@/lib/crm-utils';
import { formatCep } from '@/lib/format-br';
import { LeadCadastroForm } from '@/components/crm-vendas/LeadCadastroForm';
import { EMPTY_FORM_LEAD } from '@/components/crm-vendas/modals/ModalLeadForm';
import { useCrmCepCnpjLookup } from '@/hooks/crm-vendas/useCrmCepCnpjLookup';

export default function NovoLeadPage() {
  const params = useParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const basePath = `/loja/${slug}/crm-vendas/leads`;
  const { origensAtivas } = useCRMConfig();
  const [form, setForm] = useState(EMPTY_FORM_LEAD);
  const [enviando, setEnviando] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);

  const { handleBuscarCnpj, handleBuscarCep, buscarCepLoading, buscarCnpjLoading } =
    useCrmCepCnpjLookup<typeof form>((updater) => setForm(updater), { upperCaseEndereco: true });

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
      .post('/crm-vendas/leads/', buildCrmLeadPayload(form))
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
      />
    </div>
  );
}
