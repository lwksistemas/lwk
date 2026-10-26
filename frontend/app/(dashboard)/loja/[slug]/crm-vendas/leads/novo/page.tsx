'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import { STATUS_LEAD_OPCOES } from '@/constants/crm';
import { buildCrmLeadPayload, getCrmApiErrorDetail } from '@/lib/crm-utils';
import { formatCep, formatCpf } from '@/lib/format-br';
import { LeadCadastroForm } from '@/components/crm-vendas/LeadCadastroForm';
import { EMPTY_FORM_LEAD } from '@/lib/crm-lead-form-types';
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

  const { handleBuscarCep, buscarCepLoading } =
    useCrmCepCnpjLookup<typeof form>((updater) => setForm(updater), { upperCaseEndereco: true });

  const voltarLista = () => {
    router.push(basePath);
  };

  const handleCpfChange = (value: string) => {
    setForm((f) => ({ ...f, cpf_cnpj: formatCpf(value) }));
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
    const cpf = form.cpf_cnpj.replace(/\D/g, '');
    if (cpf && cpf.length !== 11) {
      setFormErro('Informe o CPF com 11 dígitos.');
      return;
    }
    setEnviando(true);
    apiClient
      .post('/crm-vendas/leads/', buildCrmLeadPayload(form))
      .then(() => {
        router.push(basePath);
      })
      .catch((err) => {
        setFormErro(getCrmApiErrorDetail(err, 'Erro ao salvar lead.'));
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
        onCepChange={handleCepChange}
        onBuscarCep={() => handleBuscarCep(form.cep)}
        onCpfChange={handleCpfChange}
        empresaHref={`/loja/${slug}/crm-vendas/customers/nova-conta`}
        onSave={handleSave}
        onCancel={voltarLista}
      />
    </div>
  );
}
