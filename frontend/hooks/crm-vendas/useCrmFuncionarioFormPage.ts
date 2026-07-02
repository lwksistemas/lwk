'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail } from '@/lib/crm-utils';
import { formatTelefone } from '@/lib/format-br';
import { useToast } from '@/components/ui/Toast';
import {
  buildFuncionarioPayload,
  EMPTY_FUNCIONARIO_FORM,
  suggestLoginFromNome,
  type CrmFuncionario,
  type CrmFuncionarioFormData,
  type CrmFuncionarioGrupo,
  type CrmPermissaoCategoria,
} from '@/lib/crm-funcionarios';

export function useCrmFuncionarioFormPage(slug: string, vendedorId?: number) {
  const router = useRouter();
  const toast = useToast();
  const listPath = `/loja/${slug}/crm-vendas/configuracoes/funcionarios`;
  const editing = Boolean(vendedorId);

  const [form, setForm] = useState<CrmFuncionarioFormData>(EMPTY_FUNCIONARIO_FORM);
  const [grupos, setGrupos] = useState<CrmFuncionarioGrupo[]>([]);
  const [permissoesCategorias, setPermissoesCategorias] = useState<CrmPermissaoCategoria[]>([]);
  const [loadingMeta, setLoadingMeta] = useState(true);
  const [loadingVendedor, setLoadingVendedor] = useState(editing);
  const [salvando, setSalvando] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoadingMeta(true);
        const [resGrupos, resPerm] = await Promise.all([
          apiClient.get<CrmFuncionarioGrupo[]>('/crm-vendas/vendedores/grupos_disponiveis/'),
          apiClient.get<CrmPermissaoCategoria[]>('/crm-vendas/vendedores/permissoes_disponiveis/'),
        ]);
        if (!cancelled) {
          setGrupos(resGrupos.data || []);
          setPermissoesCategorias(resPerm.data || []);
        }
      } catch {
        if (!cancelled) {
          setGrupos([]);
          setPermissoesCategorias([]);
        }
      } finally {
        if (!cancelled) setLoadingMeta(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!vendedorId) return;
    let cancelled = false;
    (async () => {
      try {
        setLoadingVendedor(true);
        const { data } = await apiClient.get<CrmFuncionario>(`/crm-vendas/vendedores/${vendedorId}/`);
        if (cancelled) return;
        setForm({
          nome: data.nome,
          email: data.email || '',
          telefone: formatTelefone(data.telefone || ''),
          cargo: data.cargo || 'Vendedor',
          comissao_padrao: data.comissao_padrao?.toString() || '0',
          grupo_id: data.grupo_id ? String(data.grupo_id) : '',
          criar_acesso: false,
          username: '',
          permissoes_ids: data.permissoes_ids || [],
        });
      } catch (err: unknown) {
        if (!cancelled) {
          setFormErro(getCrmApiErrorDetail(err, 'Erro ao carregar funcionário.'));
        }
      } finally {
        if (!cancelled) setLoadingVendedor(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [vendedorId]);

  const handleGrupoChange = useCallback(
    (grupoId: string) => {
      setForm((prev) => {
        const grupo = grupos.find((g) => String(g.id) === grupoId);
        return {
          ...prev,
          grupo_id: grupoId,
          permissoes_ids: grupo?.permissoes_ids ? [...grupo.permissoes_ids] : [],
        };
      });
    },
    [grupos],
  );

  const togglePermissao = useCallback((permId: number, checked: boolean) => {
    setForm((prev) => {
      const set = new Set(prev.permissoes_ids);
      if (checked) set.add(permId);
      else set.delete(permId);
      return { ...prev, permissoes_ids: Array.from(set).sort((a, b) => a - b) };
    });
  }, []);

  const toggleCriarAcesso = useCallback((checked: boolean) => {
    setForm((prev) => ({
      ...prev,
      criar_acesso: checked,
      username:
        checked && !prev.username ? suggestLoginFromNome(prev.nome) : prev.username,
    }));
  }, []);

  const validateForm = useCallback(() => {
    if (!form.nome.trim()) {
      toast.warning('Informe o nome.');
      return false;
    }
    if (form.criar_acesso && !form.username?.trim()) {
      toast.warning('Para criar acesso, informe o usuário para login.');
      return false;
    }
    if (form.criar_acesso && !form.email?.trim()) {
      toast.warning('Para criar acesso, informe o e-mail.');
      return false;
    }
    return true;
  }, [form, toast]);

  const handleSave = async () => {
    setFormErro(null);
    if (!validateForm()) return;

    setSalvando(true);
    try {
      const payload = buildFuncionarioPayload(form);
      if (editing && vendedorId) {
        await apiClient.patch(`/crm-vendas/vendedores/${vendedorId}/`, payload);
      } else {
        await apiClient.post('/crm-vendas/vendedores/', payload);
      }
      router.push(`${listPath}?saved=1`);
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { nome?: string[]; detail?: string } } };
      setFormErro(
        ax.response?.data?.nome?.[0] ||
          getCrmApiErrorDetail(err, 'Erro ao salvar funcionário.'),
      );
    } finally {
      setSalvando(false);
    }
  };

  const voltarLista = () => router.push(listPath);

  return {
    editing,
    form,
    setForm,
    grupos,
    permissoesCategorias,
    loadingMeta,
    loadingVendedor,
    salvando,
    formErro,
    handleGrupoChange,
    togglePermissao,
    toggleCriarAcesso,
    handleSave,
    voltarLista,
  };
}
