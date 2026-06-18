/**
 * Formulário e carregamento de clientes para emissão NFS-e (modal loja CRM).
 */
import apiClient from '@/lib/api-client';
import { consultaCnpj } from '@/lib/consulta-cnpj';
import { ensureArray } from '@/lib/array-helpers';
import { fetchAllPaginatedResults } from '@/lib/crm-utils';

export const NFSE_EMISSAO_INPUT_CLASS =
  'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#0d1f3c] text-gray-900 dark:text-white';

export const NFSE_EMISSAO_INITIAL_FORM = {
  conta_id: null as number | null,
  empresa_prestadora_id: null as number | null,
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
  item_lista_servico: '',
};

export type NfseDefaultsServico = {
  servico_descricao: string;
  codigo_cnae: string;
  codigo_servico: string;
  item_lista_servico: string;
};

export function defaultsServicoFromCrmConfig(config: {
  descricao_servico_padrao?: string;
  codigo_servico_municipal?: string;
  codigo_cnae?: string;
  item_lista_servico?: string;
} | null): NfseDefaultsServico {
  return {
    servico_descricao: config?.descricao_servico_padrao || '',
    codigo_servico: config?.codigo_servico_municipal || '',
    codigo_cnae: config?.codigo_cnae || '',
    item_lista_servico: config?.item_lista_servico || '',
  };
}

export type NfseEmissaoContaOption = {
  id: number | string;
  _tipo: 'conta' | 'lead';
  _fonte?: 'conta' | 'lead' | 'nfse' | 'brasilapi';
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

export type NfsePrestadoraOption = {
  id: number;
  nome: string;
  razao_social?: string;
  cnpj?: string;
  _display: string;
};

export function somenteDigitosDocumento(value: string): string {
  return (value || '').replace(/\D/g, '');
}

/** Busca tomador (conta ou lead) pelo CPF/CNPJ informado em lista já carregada. */
export function buscarTomadorPorDocumento(
  contas: NfseEmissaoContaOption[],
  documento: string,
): NfseEmissaoContaOption | null {
  const digits = somenteDigitosDocumento(documento);
  if (digits.length < 11) return null;
  return (
    contas.find((c) => somenteDigitosDocumento(c.cnpj || '') === digits) ?? null
  );
}

function mapContaTomadorFromApi(c: Record<string, unknown>, documento: string): NfseEmissaoContaOption {
  return {
    id: c.id as number,
    _tipo: 'conta',
    nome: String(c.nome || ''),
    razao_social: String(c.razao_social || c.nome || ''),
    cnpj: String(c.cnpj || documento),
    email: String(c.email || ''),
    logradouro: String(c.logradouro || ''),
    numero: String(c.numero || ''),
    complemento: String(c.complemento || ''),
    bairro: String(c.bairro || ''),
    cidade: String(c.cidade || ''),
    uf: String(c.uf || ''),
    cep: String(c.cep || ''),
    _display: String(c.razao_social || c.nome || ''),
    _fonte: 'conta',
  };
}

function mapLeadTomadorFromApi(l: Record<string, unknown>, documento: string): NfseEmissaoContaOption {
  const contaId = l.conta as number | undefined;
  const contaCnpj = String(l.conta_cnpj || '');
  if (contaId && contaCnpj) {
    return mapContaTomadorFromApi(
      {
        id: contaId,
        nome: l.conta_nome,
        razao_social: l.conta_razao_social || l.conta_nome,
        cnpj: contaCnpj,
        email: l.email,
        logradouro: l.logradouro,
        numero: l.numero,
        complemento: l.complemento,
        bairro: l.bairro,
        cidade: l.cidade,
        uf: l.uf,
        cep: l.cep,
      },
      documento,
    );
  }
  const empresa = String(l.empresa || l.nome || '');
  return {
    id: `lead_${l.id}`,
    _tipo: 'lead',
    _lead_id: l.id as number,
    nome: empresa,
    razao_social: empresa,
    cnpj: String(l.cpf_cnpj || documento),
    email: String(l.email || ''),
    logradouro: String(l.logradouro || ''),
    numero: String(l.numero || ''),
    complemento: String(l.complemento || ''),
    bairro: String(l.bairro || ''),
    cidade: String(l.cidade || ''),
    uf: String(l.uf || ''),
    cep: String(l.cep || ''),
    _display: empresa,
    _fonte: 'lead',
  };
}

/** Busca em Clientes e Leads do CRM (?documento=). */
async function buscarTomadorNoCrm(documento: string): Promise<NfseEmissaoContaOption | null> {
  const digits = somenteDigitosDocumento(documento);
  if (digits.length !== 11 && digits.length !== 14) return null;

  const params = { documento: digits, page_size: 10 };
  try {
    const [resContas, resLeads] = await Promise.all([
      apiClient.get('/crm-vendas/contas/', { params }),
      apiClient.get('/crm-vendas/leads/', { params }),
    ]);
    const contas = ensureArray<Record<string, unknown>>(resContas.data);
    if (contas.length > 0) {
      return mapContaTomadorFromApi(contas[0], documento);
    }
    const leads = ensureArray<Record<string, unknown>>(resLeads.data);
    if (leads.length > 0) {
      return mapLeadTomadorFromApi(leads[0], documento);
    }
  } catch {
    // fallback em outras fontes
  }
  return null;
}

/** Busca tomador em NFS-e já emitidas (fallback alinhado ao filtro da listagem). */
async function buscarTomadorNaListaNfse(
  documento: string,
): Promise<NfseEmissaoContaOption | null> {
  const digits = somenteDigitosDocumento(documento);
  if (digits.length !== 11 && digits.length !== 14) return null;

  const buscas = [digits, digits.slice(0, 8), documento.replace(/\D/g, '').slice(-4)];
  for (const busca of buscas) {
    if (!busca) continue;
    try {
      const res = await apiClient.get('/nfse/', { params: { busca } });
      const lista = ensureArray<Record<string, unknown>>(res.data);
      for (const nf of lista) {
        const docNf = somenteDigitosDocumento(String(nf.tomador_cpf_cnpj || ''));
        const match =
          docNf === digits ||
          (docNf.length > 0 &&
            digits.length === 14 &&
            docNf.padStart(14, '0') === digits.padStart(14, '0'));
        if (match && nf.tomador_nome) {
          return {
            id: `nfse_${nf.id ?? digits}`,
            _tipo: 'lead',
            nome: String(nf.tomador_nome || ''),
            razao_social: String(nf.tomador_nome || ''),
            cnpj: String(nf.tomador_cpf_cnpj || documento),
            email: String(nf.tomador_email || ''),
            _display: String(nf.tomador_nome || ''),
            _fonte: 'nfse',
          };
        }
      }
    } catch {
      // tenta próximo padrão de busca
    }
  }
  return null;
}

/** Busca tomador no CRM, NFS-e emitidas ou Receita Federal (CNPJ). */
export async function buscarTomadorCadastroPorDocumento(
  documento: string,
): Promise<NfseEmissaoContaOption | null> {
  const digits = somenteDigitosDocumento(documento);
  if (digits.length !== 11 && digits.length !== 14) return null;

  try {
    const res = await apiClient.get('/nfse/buscar-tomador/', {
      params: { documento: digits },
    });
    const d = res.data as Record<string, unknown>;
    if (d?.encontrado) {
      const fonte = String(d.fonte || '');
      const contaId = d.conta_id as number | undefined;
      return {
        id: contaId ?? `${fonte}_${digits}`,
        _tipo: fonte === 'conta' ? 'conta' : 'lead',
        nome: String(d.nome || ''),
        razao_social: String(d.nome || ''),
        cnpj: String(d.cpf_cnpj || documento),
        email: String(d.email || ''),
        logradouro: String(d.logradouro || ''),
        numero: String(d.numero || ''),
        complemento: String(d.complemento || ''),
        bairro: String(d.bairro || ''),
        cidade: String(d.cidade || ''),
        uf: String(d.uf || ''),
        cep: String(d.cep || ''),
        _display: String(d.nome || ''),
        _fonte: fonte as NfseEmissaoContaOption['_fonte'],
      };
    }
  } catch {
    // segue para CRM direto
  }

  const crm = await buscarTomadorNoCrm(documento);
  if (crm) return crm;

  const nfseLista = await buscarTomadorNaListaNfse(documento);
  if (nfseLista) return nfseLista;

  if (digits.length === 14) {
    const dados = await consultaCnpj(documento);
    if (dados?.razao_social) {
      return {
        id: `brasilapi_${digits}`,
        _tipo: 'lead',
        nome: dados.nome_fantasia || dados.razao_social,
        razao_social: dados.razao_social,
        cnpj: documento,
        email: '',
        logradouro: dados.logradouro || '',
        numero: dados.numero || '',
        complemento: dados.complemento || '',
        bairro: dados.bairro || '',
        cidade: dados.municipio || '',
        uf: dados.uf || '',
        cep: dados.cep || '',
        _display: dados.razao_social,
        _fonte: 'brasilapi',
      };
    }
  }

  return null;
}

export function preencherFormTomador(
  conta: NfseEmissaoContaOption,
): Partial<typeof NFSE_EMISSAO_INITIAL_FORM> {
  return {
    conta_id: conta._tipo === 'conta' ? Number(conta.id) : null,
    tomador_cpf_cnpj: conta.cnpj || '',
    tomador_nome: conta.razao_social || conta.nome || '',
    tomador_email: conta.email || '',
    tomador_logradouro: conta.logradouro || '',
    tomador_numero: conta.numero || '',
    tomador_complemento: conta.complemento || '',
    tomador_bairro: conta.bairro || '',
    tomador_cidade: conta.cidade || '',
    tomador_uf: conta.uf || '',
    tomador_cep: conta.cep || '',
  };
}

/** Empresas prestadoras cadastradas no CRM (tipo prestadora / ambos). */
export async function carregarPrestadorasParaNfse(): Promise<NfsePrestadoraOption[]> {
  const res = await apiClient.get('/crm-vendas/contas/', { params: { tipo: 'prestadora' } });
  return ensureArray<Record<string, unknown>>(res.data).map((c) => {
    const nome = String(c.nome || '');
    const razao = String(c.razao_social || '');
    const cnpj = String(c.cnpj || '');
    const label = razao || nome;
    return {
      id: c.id as number,
      nome,
      razao_social: razao,
      cnpj,
      _display: `${label}${cnpj ? ` — ${cnpj}` : ''}`,
    };
  });
}

/** Carrega todas as contas com CNPJ + leads — qualquer empresa pode ser tomador. */
export async function carregarContasTomadorParaNfse(): Promise<NfseEmissaoContaOption[]> {
  const [contasRaw, leadsRaw] = await Promise.all([
    fetchAllPaginatedResults<Record<string, unknown>>('/crm-vendas/contas/'),
    fetchAllPaginatedResults<Record<string, unknown>>('/crm-vendas/leads/'),
  ]);
  const contasList = contasRaw.map((c) => ({
    ...c,
    id: c.id as number,
    _tipo: 'conta' as const,
    _display: `${c.nome}${c.cnpj ? ` - ${c.cnpj}` : ''}`,
  })) as NfseEmissaoContaOption[];
  const leadsList = leadsRaw
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

/** @deprecated Use carregarContasTomadorParaNfse */
export async function carregarContasLeadsParaNfse(): Promise<NfseEmissaoContaOption[]> {
  return carregarContasTomadorParaNfse();
}
