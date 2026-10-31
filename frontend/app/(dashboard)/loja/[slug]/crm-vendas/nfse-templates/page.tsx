'use client';

import { FileText } from 'lucide-react';
import CrmTemplatesManagerPage from '@/components/crm-vendas/CrmTemplatesManagerPage';

export default function NfseTemplatesPage() {
  return (
    <CrmTemplatesManagerPage
      apiSegment="nfse-templates"
      title="Templates de Descrição NFS-e"
      subtitle="Cada empresa prestadora tem o próprio texto. A nota usa o template da empresa escolhida."
      vincularPrestadora
      namePlaceholder="Ex: Consultoria mensal, Treinamento in-company"
      EmptyStateIcon={FileText}
    />
  );
}
