'use client';

import { useEffect } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { CrmFormPageShell } from '@/components/crm-vendas/CrmFormPageShell';
import { ContatoFormFields } from '@/components/crm-vendas/ContatoFormFields';
import { useCrmContatoFormPage } from '@/hooks/crm-vendas/useCrmContatoFormPage';

export default function NovoContatoPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const slug = (params?.slug as string) ?? '';
  const contaId = searchParams.get('conta_id') || '';
  const contaNome = searchParams.get('conta_nome') || '';

  const { formData, setFormData, contaNomeForm, saving, error, loading, salvar, aplicarContaInicial, voltar } =
    useCrmContatoFormPage(slug);

  useEffect(() => {
    if (contaId) aplicarContaInicial(contaId, contaNome || undefined);
  }, [aplicarContaInicial, contaId, contaNome]);

  if (loading) {
    return (
      <div className="-m-4 sm:-m-6 lg:-m-8 flex flex-1 items-center justify-center min-h-[calc(100dvh-3.5rem)] bg-[#f3f2f2] dark:bg-[#0d1f3c]">
        <p className="text-gray-500 dark:text-gray-400">Carregando...</p>
      </div>
    );
  }

  return (
    <CrmFormPageShell
      error={error}
      saving={saving}
      saveLabel="Criar contato"
      savingLabel="Salvando..."
      onSave={salvar}
      onCancel={voltar}
    >
      <div className="space-y-6 max-w-3xl">
        <div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-white">Novo contato</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Pessoa vinculada a uma conta. Ao salvar, um lead é criado automaticamente.
          </p>
        </div>
        <ContatoFormFields
          layout="page"
          formData={formData}
          contaNomeInicial={contaNomeForm || contaNome}
          disabled={saving}
          onChange={setFormData}
        />
      </div>
    </CrmFormPageShell>
  );
}
