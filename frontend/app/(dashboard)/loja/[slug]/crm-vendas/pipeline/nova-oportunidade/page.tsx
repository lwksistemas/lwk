'use client';

/**
 * Página dedicada para criação de oportunidade — CRM Vendas.
 */

import { useParams, useRouter, useSearchParams } from 'next/navigation';
import OportunidadeFormFields from '@/components/crm-vendas/OportunidadeFormFields';
import { CrmFormPageShell } from '@/components/crm-vendas/CrmFormPageShell';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import { useOportunidadeForm } from '@/hooks/crm-vendas/useOportunidadeForm';

export default function NovaOportunidadePage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = (params?.slug as string) ?? '';
  const pipelinePath = `/loja/${slug}/crm-vendas/pipeline`;
  const { etapasAtivas } = useCRMConfig();
  const etapas = etapasAtivas();
  const initialLeadId = searchParams.get('lead_id') || '';

  const formState = useOportunidadeForm({ initialLeadId, enabled: true });
  const { enviando, formErro, loading, leads, criarOportunidade } = formState;

  const handleSave = async () => {
    const id = await criarOportunidade();
    if (id) router.push(pipelinePath);
  };

  if (loading) {
    return (
      <div className="-m-4 sm:-m-6 lg:-m-8 flex flex-1 items-center justify-center min-h-[calc(100dvh-3.5rem)] bg-[#f3f2f2] dark:bg-[#0d1f3c]">
        <p className="text-gray-500 dark:text-gray-400">Carregando...</p>
      </div>
    );
  }

  return (
    <CrmFormPageShell
      error={formErro}
      saving={enviando}
      saveLabel="Criar oportunidade"
      savingLabel="Criando..."
      onSave={handleSave}
      onCancel={() => router.push(pipelinePath)}
      saveDisabled={leads.length === 0}
    >
      <OportunidadeFormFields slug={slug} etapas={etapas} layout="page" formState={formState} />
    </CrmFormPageShell>
  );
}
