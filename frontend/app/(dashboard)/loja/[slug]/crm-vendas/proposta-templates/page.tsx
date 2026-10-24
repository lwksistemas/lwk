'use client';

import { FileText } from 'lucide-react';
import CrmTemplatesManagerPage from '@/components/crm-vendas/CrmTemplatesManagerPage';

export default function PropostaTemplatesPage() {
  return (
    <CrmTemplatesManagerPage
      apiSegment="proposta-templates"
      title="Templates de Propostas"
      subtitle="Cada template fica na prestadora. Na proposta, só aparecem os templates dela."
      namePlaceholder="Ex: Proposta Padrão, Proposta Premium"
      EmptyStateIcon={FileText}
      vincularPrestadora
    />
  );
}
