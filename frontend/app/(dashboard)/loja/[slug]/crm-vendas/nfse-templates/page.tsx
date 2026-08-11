'use client';

import { FileText } from 'lucide-react';
import CrmTemplatesManagerPage from '@/components/crm-vendas/CrmTemplatesManagerPage';

export default function NfseTemplatesPage() {
  return (
    <CrmTemplatesManagerPage
      apiSegment="nfse-templates"
      title="Templates de Descrição NFS-e"
      subtitle="Crie textos reutilizáveis para a descrição do serviço na emissão da nota"
      namePlaceholder="Ex: Consultoria mensal, Treinamento in-company"
      EmptyStateIcon={FileText}
    />
  );
}
