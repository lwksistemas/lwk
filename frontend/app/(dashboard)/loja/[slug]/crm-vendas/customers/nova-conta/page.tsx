'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { consultaCep } from '@/lib/consulta-cep';
import { consultaCnpj } from '@/lib/consulta-cnpj';
import { applyTelefoneInternacionalPayload, formatTelefone } from '@/lib/format-br';
import { ContaCadastroForm, type ContaFormData } from '@/components/crm-vendas/ContaCadastroForm';

const EMPTY_FORM: ContaFormData = {
  nome: '',
  razao_social: '',
  cnpj: '',
  inscricao_estadual: '',
  tipo: 'cliente',
  segmento: '',
  telefone: '',
  email: '',
  site: '',
  cep: '',
  logradouro: '',
  numero: '',
  complemento: '',
  bairro: '',
  cidade: '',
  uf: '',
  observacoes: '',
};

export default function NovaContaPage() {
  const params = useParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const listPath = `/loja/${slug}/crm-vendas/customers`;

  const [formData, setFormData] = useState<ContaFormData>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [consultingCNPJ, setConsultingCNPJ] = useState(false);
  const [consultingCEP, setConsultingCEP] = useState(false);

  const consultarCNPJ = async () => {
    const cnpj = formData.cnpj.replace(/\D/g, '');
    if (cnpj.length !== 14) {
      setFormErro('Informe um CNPJ válido com 14 dígitos.');
      return;
    }
    setFormErro(null);
    setConsultingCNPJ(true);
    try {
      const data = await consultaCnpj(formData.cnpj);
      if (!data) {
        setFormErro('CNPJ não encontrado ou serviço indisponível.');
        return;
      }
      setFormData((f) => ({
        ...f,
        razao_social: data.razao_social || f.razao_social,
        nome: data.nome_fantasia || data.razao_social || f.nome,
        email: data.email || f.email,
        cep: data.cep || f.cep,
        logradouro: data.logradouro || f.logradouro,
        numero: data.numero || f.numero,
        complemento: data.complemento || f.complemento,
        bairro: data.bairro || f.bairro,
        cidade: data.municipio || f.cidade,
        uf: data.uf || f.uf,
      }));
    } catch {
      setFormErro('Erro ao consultar CNPJ.');
    } finally {
      setConsultingCNPJ(false);
    }
  };

  const consultarCEP = async () => {
    const cep = formData.cep.replace(/\D/g, '');
    if (cep.length !== 8) return;
    setConsultingCEP(true);
    try {
      const endereco = await consultaCep(formData.cep);
      if (endereco) {
        setFormData((f) => ({
          ...f,
          logradouro: endereco.logradouro || f.logradouro,
          bairro: endereco.bairro || f.bairro,
          cidade: endereco.cidade || f.cidade,
          uf: endereco.uf || f.uf,
        }));
      }
    } finally {
      setConsultingCEP(false);
    }
  };

  const handleSave = async () => {
    setFormErro(null);
    if (!formData.nome.trim()) {
      setFormErro('Nome fantasia é obrigatório.');
      return;
    }
    setSaving(true);
    try {
      await apiClient.post('/crm-vendas/contas/', applyTelefoneInternacionalPayload(formData));
      router.push(listPath);
    } catch (err: unknown) {
      const resData = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
      const detail = resData?.detail as string | undefined;
      if (detail) {
        setFormErro(detail);
      } else if (resData && typeof resData === 'object') {
        // Erros de validação: {"campo": ["mensagem"]} ou {"non_field_errors": ["msg"]}
        const nonField = resData.non_field_errors;
        if (Array.isArray(nonField) && nonField.length > 0) {
          setFormErro(nonField.join(' '));
        } else {
          const msgs = Object.entries(resData)
            .filter(([k]) => k !== 'non_field_errors')
            .map(([k, v]) => {
              const msg = Array.isArray(v) ? v.join(', ') : String(v);
              return `${k}: ${msg}`;
            })
            .join(' | ');
          setFormErro(msgs || 'Erro ao salvar conta.');
        }
      } else {
        setFormErro('Erro ao salvar conta.');
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <ContaCadastroForm
      formData={formData}
      onChange={setFormData}
      error={formErro}
      saving={saving}
      consultingCNPJ={consultingCNPJ}
      consultingCEP={consultingCEP}
      onConsultarCNPJ={consultarCNPJ}
      onConsultarCEP={consultarCEP}
      onSave={handleSave}
      onCancel={() => router.push(listPath)}
    />
  );
}
