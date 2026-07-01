'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import { STATUS_LEAD_OPCOES } from '@/constants/crm';
import { consultaCep } from '@/lib/consulta-cep';
import { consultaCnpj, formatCpfCnpj } from '@/lib/consulta-cnpj';
import { useToast } from '@/components/ui/Toast';
import { buildCrmLeadPayload } from '@/lib/crm-utils';
import { formatCep, toUpperCase } from '@/lib/format-br';
import { LeadCadastroForm } from '@/components/crm-vendas/LeadCadastroForm';

export default function NovoLeadPage() {
  const toast = useToast();
  const params = useParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const basePath = `/loja/${slug}/crm-vendas/leads`;
  const { origensAtivas } = useCRMConfig();
  const [form, setForm] = useState({
    nome: '',
    empresa: '',
    cpf_cnpj: '',
    email: '',
    telefone: '',
    origem: 'site',
    status: 'novo',
    cep: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    uf: '',
    observacoes: '',
  });
  const [enviando, setEnviando] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [buscarCepLoading, setBuscarCepLoading] = useState(false);
  const [buscarCnpjLoading, setBuscarCnpjLoading] = useState(false);

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

  const handleBuscarCnpj = async () => {
    const cnpj = form.cpf_cnpj.replace(/\D/g, '');
    if (cnpj.length !== 14) {
      toast.warning('Informe um CNPJ válido com 14 dígitos para buscar.');
      return;
    }
    setBuscarCnpjLoading(true);
    try {
      const data = await consultaCnpj(form.cpf_cnpj);
      if (data) {
        setForm((f) => ({
          ...f,
          nome: data.razao_social || f.nome,
          empresa: data.nome_fantasia || f.empresa,
          cep: data.cep || f.cep,
          logradouro: data.logradouro || f.logradouro,
          numero: data.numero || f.numero,
          complemento: data.complemento || f.complemento,
          bairro: data.bairro || f.bairro,
          cidade: data.municipio || f.cidade,
          uf: data.uf || f.uf,
        }));
      } else {
        toast.warning('CNPJ não encontrado ou serviço indisponível.');
      }
    } catch {
      toast.error('Erro ao consultar CNPJ. Tente novamente.');
    } finally {
      setBuscarCnpjLoading(false);
    }
  };

  const handleCepChange = (value: string) => {
    setForm((f) => ({ ...f, cep: formatCep(value) }));
  };

  const handleBuscarCep = async () => {
    const cep = form.cep.replace(/\D/g, '');
    if (cep.length !== 8) {
      toast.warning('Informe um CEP válido com 8 dígitos.');
      return;
    }
    setBuscarCepLoading(true);
    try {
      const endereco = await consultaCep(form.cep);
      if (endereco) {
        setForm((f) => ({
          ...f,
          logradouro: toUpperCase(endereco.logradouro),
          bairro: toUpperCase(endereco.bairro),
          cidade: toUpperCase(endereco.cidade),
          uf: endereco.uf.toUpperCase(),
        }));
      } else {
        toast.error('Erro ao consultar CEP. Verifique sua conexão ou tente novamente em instantes.');
      }
    } finally {
      setBuscarCepLoading(false);
    }
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
        statusOpcoes={STATUS_LEAD_OPCOES}
        buscarCepLoading={buscarCepLoading}
        buscarCnpjLoading={buscarCnpjLoading}
        onCepChange={handleCepChange}
        onBuscarCep={handleBuscarCep}
        onBuscarCnpj={handleBuscarCnpj}
        onCpfCnpjChange={handleCpfCnpjChange}
        onSave={handleSave}
        onCancel={voltarLista}
      />
    </div>
  );
}
