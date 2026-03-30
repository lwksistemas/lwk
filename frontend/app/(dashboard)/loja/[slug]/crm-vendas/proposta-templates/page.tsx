'use client';

import { FileText } from 'lucide-react';
import CrmTemplatesManagerPage from '@/components/crm-vendas/CrmTemplatesManagerPage';

export default function PropostaTemplatesPage() {
  return (
    <CrmTemplatesManagerPage
      apiSegment="proposta-templates"
      title="Templates de Propostas"
      subtitle="Crie templates reutilizáveis para suas propostas comerciais"
      namePlaceholder="Ex: Proposta Padrão, Proposta Premium"
      EmptyStateIcon={FileText}
    />
  );
}
