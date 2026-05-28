/**
 * Formulário e carregamento de clientes para emissão NFS-e (modal loja CRM).
 */
import apiClient from '@/lib/api-client';
import { ensureArray } from '@/lib/array-helpers';

export const NFSE_EMISSAO_INPUT_CLASS =
  'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white';

export const NFSE_EMISSAO_INITIAL_FORM = {
  conta_id: null as number | null,
  tomador_cpf_cnpj: '',
  tomador_nome: '',
  tomador_email: '',
  tomador_logradouro: '',
  tomador_numero: '',
  tomador_complemento: '',
  tomador_bairro: '',
  tomador_cidade: '',
  tomador_uf: '',
  tomador_cep: '',
  servico_descricao: '',
  valor_servicos: '',
  enviar_email: true,
  codigo_cnae: '',
  codigo_servico: '',
};

export type NfseEmissaoContaOption = {
  id: number | string;
  _tipo: 'conta' | 'lead';
  _display?: string;
  _lead_id?: number;
  nome?: string;
  razao_social?: string;
  cnpj?: string;
  email?: string;
  logradouro?: string;
  numero?: string;
  complemento?: string;
  bairro?: string;
  cidade?: string;
  uf?: string;
  cep?: string;
};

/** Carrega contas CRM + leads com CPF/CNPJ para seleção no modal de emissão. */
export async function carregarContasLeadsParaNfse(): Promise<NfseEmissaoContaOption[]> {
  const [resContas, resLeads] = await Promise.all([
    apiClient.get('/crm-vendas/contas/'),
    apiClient.get('/crm-vendas/leads/'),
  ]);
  const contasList = ensureArray<Record<string, unknown>>(resContas.data).map((c) => ({
    ...c,
    id: c.id as number,
    _tipo: 'conta' as const,
    _display: `${c.nome}${c.cnpj ? ` - ${c.cnpj}` : ''}`,
  })) as NfseEmissaoContaOption[];
  const leadsList = ensureArray<Record<string, unknown>>(resLeads.data)
    .filter((l) => l.cpf_cnpj)
    .map((l) => ({
      id: `lead_${l.id}`,
      _tipo: 'lead' as const,
      _lead_id: l.id as number,
      nome: l.nome as string,
      cnpj: (l.cpf_cnpj as string) || '',
      razao_social: l.nome as string,
      email: (l.email as string) || '',
      logradouro: (l.logradouro as string) || '',
      numero: (l.numero as string) || '',
      complemento: (l.complemento as string) || '',
      bairro: (l.bairro as string) || '',
      cidade: (l.cidade as string) || '',
      uf: (l.uf as string) || '',
      cep: (l.cep as string) || '',
      _display: `${l.nome}${l.cpf_cnpj ? ` - ${l.cpf_cnpj}` : ''}`,
    })) as NfseEmissaoContaOption[];
  return [...contasList, ...leadsList];
}
