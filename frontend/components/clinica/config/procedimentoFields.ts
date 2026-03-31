import { FieldConfig } from '@/components/shared/GenericCrudModal';

export const procedimentoFields: FieldConfig[] = [
  { 
    name: 'nome', 
    label: 'Nome do Procedimento', 
    type: 'text', 
    required: true,
    placeholder: 'Ex: Limpeza de Pele Profunda'
  },
  { 
    name: 'categoria', 
    label: 'Categoria', 
    type: 'select', 
    required: true,
    options: [
      { value: 'Facial', label: 'Facial' },
      { value: 'Corporal', label: 'Corporal' },
      { value: 'Capilar', label: 'Capilar' },
      { value: 'Massagem', label: 'Massagem' },
      { value: 'Depilação', label: 'Depilação' },
      { value: 'Outro', label: 'Outro' },
    ]
  },
  { 
    name: 'duracao', 
    label: 'Duração (minutos)', 
    type: 'number', 
    required: true,
    placeholder: '60'
  },
  { 
    name: 'preco', 
    label: 'Preço (R$)', 
    type: 'number', 
    required: true,
    placeholder: '80.00'
  },
  { 
    name: 'descricao', 
    label: 'Descrição', 
    type: 'textarea', 
    required: true,
    rows: 3,
    placeholder: 'Descreva o procedimento e seus benefícios...'
  },
];
