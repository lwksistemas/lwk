'use client';

import { useParams } from 'next/navigation';
import { VendedorCadastroForm } from '@/components/crm-vendas/VendedorCadastroForm';
import { useCrmFuncionarioFormPage } from '@/hooks/crm-vendas/useCrmFuncionarioFormPage';

export default function NovoFuncionarioPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const listPath = `/loja/${slug}/crm-vendas/configuracoes/funcionarios`;

  const {
    form,
    setForm,
    grupos,
    permissoesCategorias,
    loadingMeta,
    salvando,
    formErro,
    handleGrupoChange,
    togglePermissao,
    toggleCriarAcesso,
    handleSave,
    voltarLista,
  } = useCrmFuncionarioFormPage(slug);

  return (
    <VendedorCadastroForm
      listHref={listPath}
      form={form}
      setForm={setForm}
      grupos={grupos}
      permissoesCategorias={permissoesCategorias}
      loading={loadingMeta}
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
