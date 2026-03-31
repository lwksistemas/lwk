import { FieldConfig } from '@/components/shared/GenericCrudModal';

export const clienteFields: FieldConfig[] = [
  { 
    name: 'nome', 
    label: 'Nome Completo', 
    type: 'text', 
    required: true,
    placeholder: 'Nome completo do paciente'
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
    name: 'cpf', 
    label: 'CPF', 
    type: 'text',
    placeholder: '000.000.000-00',
    maxLength: 14
  },
  { 
    name: 'data_nascimento', 
    label: 'Data de Nascimento', 
    type: 'date'
  },
  { 
    name: 'endereco', 
    label: 'Endereço', 
    type: 'text',
    placeholder: 'Rua, número, bairro'
  },
  { 
    name: 'cidade', 
    label: 'Cidade', 
    type: 'text',
    placeholder: 'Nome da cidade'
  },
  { 
    name: 'estado', 
    label: 'Estado', 
    type: 'select',
    options: [
      { value: 'AC', label: 'Acre' },
      { value: 'AL', label: 'Alagoas' },
      { value: 'AP', label: 'Amapá' },
      { value: 'AM', label: 'Amazonas' },
      { value: 'BA', label: 'Bahia' },
      { value: 'CE', label: 'Ceará' },
      { value: 'DF', label: 'Distrito Federal' },
      { value: 'ES', label: 'Espírito Santo' },
      { value: 'GO', label: 'Goiás' },
      { value: 'MA', label: 'Maranhão' },
      { value: 'MT', label: 'Mato Grosso' },
      { value: 'MS', label: 'Mato Grosso do Sul' },
      { value: 'MG', label: 'Minas Gerais' },
      { value: 'PA', label: 'Pará' },
      { value: 'PB', label: 'Paraíba' },
      { value: 'PR', label: 'Paraná' },
      { value: 'PE', label: 'Pernambuco' },
      { value: 'PI', label: 'Piauí' },
      { value: 'RJ', label: 'Rio de Janeiro' },
      { value: 'RN', label: 'Rio Grande do Norte' },
      { value: 'RS', label: 'Rio Grande do Sul' },
      { value: 'RO', label: 'Rondônia' },
      { value: 'RR', label: 'Roraima' },
      { value: 'SC', label: 'Santa Catarina' },
      { value: 'SP', label: 'São Paulo' },
      { value: 'SE', label: 'Sergipe' },
      { value: 'TO', label: 'Tocantins' },
    ]
  },
  { 
    name: 'observacoes', 
    label: 'Observações', 
    type: 'textarea',
    rows: 3,
    placeholder: 'Informações adicionais sobre o paciente'
  },
];
