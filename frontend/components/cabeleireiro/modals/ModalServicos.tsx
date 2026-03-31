'use client';

import { GenericCrudModal } from '@/components/shared/GenericCrudModal';
import { servicoFields } from '@/components/cabeleireiro/config/servicoFields';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

interface ModalServicosProps {
  loja: LojaInfo;
  onClose: () => void;
  onSuccess?: () => void;
}

export function ModalServicos({ loja, onClose, onSuccess }: ModalServicosProps) {
  // Transformar dados antes de salvar
  const transformDataBeforeSave = (data: any) => ({
    nome: data.nome,
    descricao: data.descricao || null,
    categoria: data.categoria,
    duracao_minutos: parseInt(data.duracao_minutos),
    preco: parseFloat(data.preco),
    is_active: true,
  });

  return (
    <GenericCrudModal
      title="Serviços"
      endpoint="/cabeleireiro/servicos/"
      fields={servicoFields}
      loja={loja}
      onClose={onClose}
      onSuccess={onSuccess}
      transformDataBeforeSave={transformDataBeforeSave}
    />
  );
}
