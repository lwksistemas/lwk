'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { applyTelefoneInternacionalPayload, formatTelefone } from '@/lib/format-br';
import { getCrmApiErrorDetail } from '@/lib/crm-utils';
import { useToast } from '@/components/ui/Toast';
import {
  EMPTY_CONTATO_FORM,
  type CrmContatoFormData,
} from '@/lib/crm-contato-form-types';
import type { CrmContato } from '@/hooks/crm-vendas/useCrmContatosPage';

export function useCrmContatoFormPage(slug: string, contatoId?: number) {
  const toast = useToast();
  const router = useRouter();
  const basePath = `/loja/${slug}/crm-vendas/contatos`;
  const editing = contatoId != null && !Number.isNaN(contatoId);

  const [formData, setFormData] = useState<CrmContatoFormData>(EMPTY_CONTATO_FORM);
  const [contaNomeForm, setContaNomeForm] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(editing);

  useEffect(() => {
    if (!editing || contatoId == null) return;
    let cancelled = false;
    setLoading(true);
    apiClient
      .get<CrmContato>(`/crm-vendas/contatos/${contatoId}/`)
      .then((res) => {
        if (cancelled) return;
        const c = res.data;
        setFormData({
          nome: c.nome || '',
          email: c.email || '',
          telefone: formatTelefone(c.telefone || ''),
          cargo: c.cargo || '',
          conta: String(c.conta) || '',
          observacoes: c.observacoes || '',
        });
        setContaNomeForm(c.conta_nome || '');
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
  }, [basePath, contatoId, editing, router]);

  const aplicarContaInicial = useCallback((contaId: string, contaNome?: string) => {
    if (!contaId) return;
    setFormData((f) => ({ ...f, conta: contaId }));
    if (contaNome) setContaNomeForm(contaNome);
  }, []);

  const salvar = useCallback(async () => {
    setError(null);
    if (!formData.nome.trim()) {
      setError('Nome é obrigatório.');
      return;
    }
    if (!formData.conta) {
      setError('Conta é obrigatória.');
      return;
    }

    setSaving(true);
    try {
      const payload = applyTelefoneInternacionalPayload({
        ...formData,
        conta: parseInt(formData.conta, 10),
      });

      if (editing && contatoId != null) {
        await apiClient.put(`/crm-vendas/contatos/${contatoId}/`, payload);
        toast.success('Contato atualizado.');
        router.push(basePath);
        return;
      }

      const res = await apiClient.post('/crm-vendas/contatos/', payload);
      const novoContato = res.data;
      try {
        const contaRes = await apiClient.get(`/crm-vendas/contas/${payload.conta}/`);
        const conta = contaRes.data;
        await apiClient.post('/crm-vendas/leads/', {
          nome: novoContato.nome,
          empresa: conta.nome,
          email: novoContato.email || conta.email || '',
          telefone: novoContato.telefone || conta.telefone || '',
          origem: 'site',
          status: 'novo',
          conta: conta.id,
          contato: novoContato.id,
          cpf_cnpj: conta.cnpj || '',
          cep: conta.cep || '',
          logradouro: conta.logradouro || '',
          numero: conta.numero || '',
          complemento: conta.complemento || '',
          bairro: conta.bairro || '',
          cidade: conta.cidade || '',
          uf: conta.uf || '',
        });
        toast.success('Contato e lead criados com sucesso!');
      } catch (leadErr: unknown) {
        toast.warning(
          `Contato criado, mas o lead automático falhou: ${getCrmApiErrorDetail(leadErr, 'erro desconhecido')}`,
        );
      }
      router.push(basePath);
    } catch (err: unknown) {
      setError(getCrmApiErrorDetail(err, 'Erro ao salvar contato.'));
    } finally {
      setSaving(false);
    }
  }, [basePath, contatoId, editing, formData, router, toast]);

  return {
    formData,
    setFormData,
    contaNomeForm,
    saving,
    error,
    loading,
    editing,
    salvar,
    aplicarContaInicial,
    voltar: () => router.push(basePath),
  };
}
