'use client';

import { GenericCrudModal, LojaInfo } from '@/components/shared/GenericCrudModal';
import { procedimentoFields } from '../config/procedimentoFields';

interface ModalProcedimentosProps {
  loja: LojaInfo;
  onClose: () => void;
  onSuccess?: () => void;
}

export function ModalProcedimentos({ loja, onClose, onSuccess }: ModalProcedimentosProps) {
  // Transformar dados antes de salvar
  const transformDataBeforeSave = (data: any) => {
    return {
      ...data,
      duracao: data.duracao ? parseInt(data.duracao, 10) : null,
      preco: data.preco ? parseFloat(data.preco) : null,
      descricao: data.descricao || null,
    };
  };

  // Transformar dados após carregar
  const transformDataAfterLoad = (data: any) => {
    return {
      ...data,
      duracao: data.duracao ?? data.duracao_minutos ?? '',
      preco: data.preco ?? '',
    };
  };

  return (
    <GenericCrudModal
      title="Procedimentos"
      endpoint="/clinica/procedimentos/"
      fields={procedimentoFields}
      loja={loja}
      onClose={onClose}
      onSuccess={onSuccess}
      transformDataBeforeSave={transformDataBeforeSave}
      transformDataAfterLoad={transformDataAfterLoad}
    />
  );
}
