import { FieldConfig } from '@/components/shared/GenericCrudModal';

export const funcionarioFields: FieldConfig[] = [
  { 
    name: 'nome', 
    label: 'Nome Completo', 
    type: 'text', 
    required: true,
    placeholder: 'Nome completo do funcionário'
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
    name: 'cargo', 
    label: 'Cargo', 
    type: 'text', 
    required: true,
    placeholder: 'Ex: Gerente, Recepcionista, Caixa...'
  },
  { 
    name: 'funcao', 
    label: 'Função/Permissão', 
    type: 'select', 
    required: true,
    options: [
      { value: 'administrador', label: 'Administrador' },
      { value: 'gerente', label: 'Gerente' },
      { value: 'atendente', label: 'Atendente/Recepcionista' },
      { value: 'caixa', label: 'Caixa' },
      { value: 'visualizador', label: 'Visualizador' },
    ]
  },
];
