'use client';

import { GenericCrudModal } from '@/components/shared/GenericCrudModal';
import { clienteFields } from '@/components/clinica/config/clienteFields';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria: string;
}

interface ModalClientesProps {
  loja: LojaInfo;
  onClose: () => void;
  onSuccess?: () => void;
}

export function ModalClientes({ loja, onClose, onSuccess }: ModalClientesProps) {
  // Transformar dados antes de salvar (strings vazias para null)
  const transformDataBeforeSave = (data: any) => ({
    nome: data.nome,
    telefone: data.telefone,
    email: data.email || null,
    cpf: data.cpf || null,
    data_nascimento: data.data_nascimento || null,
    endereco: data.endereco || null,
    cidade: data.cidade || null,
    estado: data.estado || null,
    observacoes: data.observacoes || null,
  });

  return (
    <GenericCrudModal
      title="Pacientes"
      endpoint="/clinica-beleza/patients/"
      fields={clienteFields}
      loja={loja}
      onClose={onClose}
      onSuccess={onSuccess}
      transformDataBeforeSave={transformDataBeforeSave}
    />
  );
}
