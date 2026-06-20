'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { consultaCep } from '@/lib/consulta-cep';
import { consultaCnpj } from '@/lib/consulta-cnpj';
import { applyTelefoneInternacionalPayload, formatTelefone } from '@/lib/format-br';
import { ContaCadastroForm, type ContaFormData } from '@/components/crm-vendas/ContaCadastroForm';

interface Conta {
  id: number;
  nome: string;
  razao_social?: string;
  cnpj?: string;
  inscricao_estadual?: string;
  tipo: string;
  segmento: string;
  telefone?: string;
  email?: string;
  site?: string;
  cep?: string;
  logradouro?: string;
  numero?: string;
  complemento?: string;
  bairro?: string;
  cidade?: string;
  uf?: string;
  observacoes?: string;
}

function contaToForm(conta: Conta): ContaFormData {
  return {
    nome: conta.nome || '',
    razao_social: conta.razao_social || '',
    cnpj: conta.cnpj || '',
    inscricao_estadual: conta.inscricao_estadual || '',
    tipo: conta.tipo || 'cliente',
    segmento: conta.segmento || '',
    telefone: formatTelefone(conta.telefone || ''),
    email: conta.email || '',
    site: conta.site || '',
    cep: conta.cep || '',
    logradouro: conta.logradouro || '',
    numero: conta.numero || '',
    complemento: conta.complemento || '',
    bairro: conta.bairro || '',
    cidade: conta.cidade || '',
    uf: conta.uf || '',
    observacoes: conta.observacoes || '',
  };
}

export default function EditarContaPage() {
  const params = useParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const id = parseInt(String(params?.id ?? ''), 10);
  const listPath = `/loja/${slug}/crm-vendas/customers`;

  const [formData, setFormData] = useState<ContaFormData | null>(null);
  const [saving, setSaving] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [consultingCNPJ, setConsultingCNPJ] = useState(false);
  const [consultingCEP, setConsultingCEP] = useState(false);

  useEffect(() => {
    if (isNaN(id)) {
      router.replace(listPath);
      return;
    }
    let cancelled = false;
    apiClient
      .get<Conta>(`/crm-vendas/contas/${id}/`)
      .then((res) => {
        if (!cancelled) setFormData(contaToForm(res.data));
      })
      .catch(() => {
        if (!cancelled) router.replace(listPath);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [id, listPath, router]);

  const consultarCNPJ = async () => {
    if (!formData) return;
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
      setFormData((f) =>
        f
          ? {
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
            }
          : f,
      );
    } catch {
      setFormErro('Erro ao consultar CNPJ.');
    } finally {
      setConsultingCNPJ(false);
    }
  };

  const consultarCEP = async () => {
    if (!formData) return;
    const cep = formData.cep.replace(/\D/g, '');
    if (cep.length !== 8) return;
    setConsultingCEP(true);
    try {
      const endereco = await consultaCep(formData.cep);
      if (endereco) {
        setFormData((f) =>
          f
            ? {
                ...f,
                logradouro: endereco.logradouro || f.logradouro,
                bairro: endereco.bairro || f.bairro,
                cidade: endereco.cidade || f.cidade,
                uf: endereco.uf || f.uf,
              }
            : f,
        );
      }
    } finally {
      setConsultingCEP(false);
    }
  };

  const handleSave = async () => {
    if (!formData) return;
    setFormErro(null);
    if (!formData.nome.trim()) {
      setFormErro('Nome fantasia é obrigatório.');
      return;
    }
    setSaving(true);
    try {
      await apiClient.put(`/crm-vendas/contas/${id}/`, applyTelefoneInternacionalPayload(formData));
      router.push(listPath);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFormErro(detail || 'Erro ao salvar conta.');
    } finally {
      setSaving(false);
    }
  };

  if (loading || !formData) {
    return (
      <div className="-m-4 sm:-m-6 lg:-m-8 flex flex-1 items-center justify-center min-h-[calc(100dvh-3.5rem)] bg-[#f3f2f2] dark:bg-[#0d1f3c]">
        <p className="text-gray-500 dark:text-gray-400">Carregando...</p>
      </div>
    );
  }

  return (
    <ContaCadastroForm
      editing
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
