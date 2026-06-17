/** Definições de colunas configuráveis nas listagens do CRM. */

export type CrmColunaDef = { key: string; label: string };

export const COLUNAS_LEADS_DISPONIVEIS: CrmColunaDef[] = [
  { key: 'nome', label: 'Nome' },
  { key: 'empresa', label: 'Empresa' },
  { key: 'email', label: 'E-mail' },
  { key: 'telefone', label: 'Telefone' },
  { key: 'origem', label: 'Origem' },
  { key: 'status', label: 'Status' },
  { key: 'valor_estimado', label: 'Valor Estimado' },
  { key: 'created_at', label: 'Data de Criação' },
];

export const COLUNAS_CONTAS_DISPONIVEIS: CrmColunaDef[] = [
  { key: 'nome', label: 'Nome da Conta' },
  { key: 'tipo', label: 'Tipo' },
  { key: 'segmento', label: 'Segmento' },
  { key: 'email', label: 'E-mail' },
  { key: 'telefone', label: 'Telefone' },
  { key: 'cidade', label: 'Cidade' },
  { key: 'cnpj', label: 'CNPJ' },
  { key: 'razao_social', label: 'Razão Social' },
  { key: 'uf', label: 'UF' },
  { key: 'created_at', label: 'Data de Cadastro' },
];

export const COLUNAS_CONTATOS_DISPONIVEIS: CrmColunaDef[] = [
  { key: 'nome', label: 'Nome' },
  { key: 'conta', label: 'Conta' },
  { key: 'cargo', label: 'Cargo' },
  { key: 'email', label: 'E-mail' },
  { key: 'telefone', label: 'Telefone' },
  { key: 'created_at', label: 'Data de Cadastro' },
];

export const DEFAULT_COLUNAS_LEADS = ['nome', 'empresa', 'telefone', 'email', 'origem', 'status', 'valor_estimado'];
export const DEFAULT_COLUNAS_CONTAS = ['nome', 'tipo', 'segmento', 'email', 'cidade'];
export const DEFAULT_COLUNAS_CONTATOS = ['nome', 'conta', 'cargo', 'email'];

export function colunasVisiveisFromConfig(
  keys: string[] | undefined | null,
  disponiveis: CrmColunaDef[],
  defaults: string[],
): CrmColunaDef[] {
  const labelMap = Object.fromEntries(disponiveis.map((c) => [c.key, c.label]));
  const resolved = keys && keys.length > 0 ? keys : defaults;
  return resolved.map((key) => ({ key, label: labelMap[key] || key }));
}
