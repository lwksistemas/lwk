'use client';

import { useParams } from 'next/navigation';
import { VendedorCadastroForm } from '@/components/crm-vendas/VendedorCadastroForm';
import { useCrmFuncionarioFormPage } from '@/hooks/crm-vendas/useCrmFuncionarioFormPage';

export default function EditarFuncionarioPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const vendedorId = parseInt(String(params?.id ?? ''), 10);
  const listPath = `/loja/${slug}/crm-vendas/configuracoes/funcionarios`;

  const {
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
  } = useCrmFuncionarioFormPage(slug, Number.isFinite(vendedorId) ? vendedorId : undefined);

  return (
    <VendedorCadastroForm
      listHref={listPath}
      editing={editing}
      form={form}
      setForm={setForm}
      grupos={grupos}
      permissoesCategorias={permissoesCategorias}
      loading={loadingMeta || loadingVendedor}
      error={formErro}
      saving={salvando}
      onGrupoChange={handleGrupoChange}
      onTogglePermissao={togglePermissao}
      onToggleCriarAcesso={toggleCriarAcesso}
      onSave={handleSave}
      onCancel={voltarLista}
    />
  );
}
