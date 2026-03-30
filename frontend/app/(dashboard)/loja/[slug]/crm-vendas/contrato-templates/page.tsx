'use client';

import { FileSignature } from 'lucide-react';
import CrmTemplatesManagerPage from '@/components/crm-vendas/CrmTemplatesManagerPage';

export default function ContratoTemplatesPage() {
  return (
    <CrmTemplatesManagerPage
      apiSegment="contrato-templates"
      title="Templates de Contratos"
      subtitle="Crie templates reutilizáveis para seus contratos"
      namePlaceholder="Ex: Contrato Padrão, Contrato Premium"
      EmptyStateIcon={FileSignature}
    />
  );
}
