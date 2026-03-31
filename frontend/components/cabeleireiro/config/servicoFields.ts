import { FieldConfig } from '@/components/shared/GenericCrudModal';

export const servicoFields: FieldConfig[] = [
  { 
    name: 'nome', 
    label: 'Nome do Serviço', 
    type: 'text', 
    required: true,
    placeholder: 'Ex: Corte Masculino'
  },
  { 
    name: 'descricao', 
    label: 'Descrição', 
    type: 'textarea',
    rows: 2,
    placeholder: 'Descrição breve do serviço'
  },
  { 
    name: 'categoria', 
    label: 'Categoria', 
    type: 'select',
    required: true,
    options: [
      { value: 'corte', label: 'Corte' },
      { value: 'coloracao', label: 'Coloração' },
      { value: 'tratamento', label: 'Tratamento' },
      { value: 'penteado', label: 'Penteado' },
      { value: 'manicure', label: 'Manicure/Pedicure' },
      { value: 'barba', label: 'Barba' },
      { value: 'depilacao', label: 'Depilação' },
      { value: 'maquiagem', label: 'Maquiagem' },
      { value: 'outros', label: 'Outros' },
    ]
  },
  { 
    name: 'duracao_minutos', 
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
    placeholder: '50.00'
  },
];
