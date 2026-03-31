'use client';

import { GenericCrudModal, LojaInfo } from '@/components/shared/GenericCrudModal';
import { funcionarioFields } from '../config/funcionarioFields';

interface ModalFuncionariosProps {
  loja: LojaInfo;
  onClose: () => void;
  onSuccess?: () => void;
}

export function ModalFuncionarios({ loja, onClose, onSuccess }: ModalFuncionariosProps) {
  // Transformar dados antes de salvar
  const transformDataBeforeSave = (data: any) => {
    return {
      ...data,
      email: data.email || null,
      data_admissao: new Date().toISOString().split('T')[0],
      is_active: true
    };
  };

  return (
    <GenericCrudModal
      title="Funcionários"
      endpoint="/clinica/funcionarios/"
      fields={funcionarioFields}
      loja={loja}
      onClose={onClose}
      onSuccess={onSuccess}
      transformDataBeforeSave={transformDataBeforeSave}
    />
  );
}
