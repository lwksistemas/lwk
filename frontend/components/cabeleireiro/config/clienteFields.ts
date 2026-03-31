import { FieldConfig } from '@/components/shared/GenericCrudModal';

export const clienteFields: FieldConfig[] = [
  { 
    name: 'nome', 
    label: 'Nome Completo', 
    type: 'text', 
    required: true,
    placeholder: 'Nome completo do cliente'
  },
  { 
    name: 'telefone', 
    label: 'Telefone', 
    type: 'tel', 
    required: true,
    placeholder: '(00) 00000-0000'
  },
  { 
    name: 'email', 
    label: 'E-mail', 
    type: 'email',
    placeholder: 'email@exemplo.com'
  },
  { 
    name: 'data_nascimento', 
    label: 'Data de Nascimento', 
    type: 'date'
  },
  { 
    name: 'observacoes', 
    label: 'Observações', 
    type: 'textarea',
    rows: 3,
    placeholder: 'Informações adicionais sobre o cliente'
  },
];
