/**
 * Consulta CNPJ para preencher dados da empresa automaticamente.
 * BrasilAPI (Minha Receita) primeiro; CNPJA quando a empresa ainda não está no dump.
 */

export interface DadosCnpj {
  razao_social: string;
  nome_fantasia?: string;
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  municipio: string;
  uf: string;
  /** Código IBGE do município (7 dígitos), quando disponível na BrasilAPI */
  codigo_municipio_ibge?: string;
  /** CNAE fiscal principal */
  cnae_fiscal?: string;
  email?: string;
  telefone?: string;
  optante_simples?: boolean;
}

const TIMEOUT_MS = 15000;

function formatCepFromApi(v: string | number | null | undefined): string {
  const n = String(v ?? '').replace(/\D/g, '');
  if (n.length !== 8) return '';
  return `${n.slice(0, 5)}-${n.slice(5)}`;
}

function asRecord(v: unknown): Record<string, unknown> | null {
  return v && typeof v === 'object' && !Array.isArray(v) ? (v as Record<string, unknown>) : null;
}

function str(v: unknown): string {
  if (v == null) return '';
  return String(v).trim();
}

function telefoneFromDdd(ddd: unknown, numero: unknown): string | undefined {
  const d = str(ddd).replace(/\D/g, '');
  const n = str(numero).replace(/\D/g, '');
  if (d && n) return `${d}${n}`;
  if (n) return n;
  return undefined;
}

function fetchWithTimeout(url: string): Promise<Response> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  return fetch(url, { signal: ctrl.signal }).finally(() => clearTimeout(t));
}

/**
 * Busca CEP pelo logradouro (ViaCEP) quando a BrasilAPI retorna CEP incompleto ou vazio.
 */
export async function consultaCepPorLogradouro(
  uf: string,
  cidade: string,
  logradouro: string,
): Promise<string> {
  const ufNorm = (uf || '').trim().toUpperCase();
  const cidadeNorm = (cidade || '').trim();
  const logradouroNorm = (logradouro || '').trim();
  if (!ufNorm || !cidadeNorm || !logradouroNorm) return '';

  try {
    const url = `https://viacep.com.br/ws/${encodeURIComponent(ufNorm)}/${encodeURIComponent(cidadeNorm)}/${encodeURIComponent(logradouroNorm)}/json/`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) return '';
    const list = await res.json();
    if (!Array.isArray(list) || list.length === 0) return '';
    const primeiro = list.find((item) => item && !item.erro && item.cep);
    if (!primeiro?.cep) return '';
    return formatCepFromApi(primeiro.cep);
  } catch {
    return '';
  }
}

/** Garante CEP com 8 dígitos a partir dos dados da BrasilAPI (+ ViaCEP se necessário). */
export async function resolverCepDadosCnpj(dados: DadosCnpj): Promise<string> {
  const direto = formatCepFromApi(dados.cep);
  if (direto.replace(/\D/g, '').length === 8) return direto;
  const via = await consultaCepPorLogradouro(dados.uf, dados.municipio, dados.logradouro);
  if (via.replace(/\D/g, '').length === 8) return via;
  return '';
}

export function mapBrasilApiCnpj(data: unknown): DadosCnpj | null {
  const row = asRecord(data);
  if (!row) return null;
  const razao = str(row.razao_social) || str(row.nome_fantasia);
  if (!razao) return null;
  const ibge = row.codigo_municipio_ibge ?? row.codigo_municipio;
  const cnae = row.cnae_fiscal;
  const simples = row.opcao_pelo_simples;
  return {
    razao_social: razao,
    nome_fantasia: str(row.nome_fantasia) || undefined,
    cep: formatCepFromApi(str(row.cep)) || '',
    logradouro: str(row.logradouro),
    numero: str(row.numero),
    complemento: str(row.complemento),
    bairro: str(row.bairro),
    municipio: str(row.municipio),
    uf: str(row.uf),
    codigo_municipio_ibge: ibge != null ? String(ibge).replace(/\D/g, '').slice(0, 7) : undefined,
    cnae_fiscal: cnae != null ? String(cnae).replace(/\D/g, '') : undefined,
    email: str(row.email) || str(row.correio_eletronico) || undefined,
    telefone: str(row.ddd_telefone_1).replace(/\D/g, '') || undefined,
    optante_simples: typeof simples === 'boolean' ? simples : undefined,
  };
}

export function mapCnpjaCnpj(data: unknown): DadosCnpj | null {
  const row = asRecord(data);
  if (!row) return null;
  const est = asRecord(row.estabelecimento);
  if (!est) return null;
  const razao = str(row.razao_social) || str(est.nome_fantasia);
  if (!razao) return null;
  const cidade = asRecord(est.cidade);
  const estado = asRecord(est.estado);
  const atividade = asRecord(est.atividade_principal);
  const simples = asRecord(row.simples);
  const ibge = cidade?.ibge_id;
  const cnae = atividade?.id ?? atividade?.subclasse;
  const optante = simples ? str(simples.simples).toLowerCase() : '';
  return {
    razao_social: razao,
    nome_fantasia: str(est.nome_fantasia) || undefined,
    cep: formatCepFromApi(str(est.cep)) || '',
    logradouro: str(est.logradouro),
    numero: str(est.numero),
    complemento: str(est.complemento),
    bairro: str(est.bairro),
    municipio: str(cidade?.nome),
    uf: str(estado?.sigla),
    codigo_municipio_ibge: ibge != null ? String(ibge).replace(/\D/g, '').slice(0, 7) : undefined,
    cnae_fiscal: cnae != null ? String(cnae).replace(/\D/g, '') : undefined,
    email: str(est.email) || undefined,
    telefone: telefoneFromDdd(est.ddd1, est.telefone1),
    optante_simples: optante === 'sim' || optante === 's' ? true : optante === 'não' || optante === 'nao' || optante === 'n' ? false : undefined,
  };
}

async function consultaFonte(
  url: string,
  mapper: (data: unknown) => DadosCnpj | null,
): Promise<DadosCnpj | null> {
  try {
    const res = await fetchWithTimeout(url);
    if (!res.ok) return null;
    return mapper(await res.json());
  } catch {
    return null;
  }
}

/**
 * Consulta CNPJ (BrasilAPI, com fallback CNPJA para empresas recém-abertas).
 * @param cnpj - CNPJ com ou sem formatação (00.000.000/0001-00 ou 00000000000100)
 * @returns Dados da empresa ou null se não encontrado/erro
 */
export async function consultaCnpj(cnpj: string): Promise<DadosCnpj | null> {
  const digits = cnpj.replace(/\D/g, '');
  if (digits.length !== 14) return null;

  return (
    (await consultaFonte(`https://brasilapi.com.br/api/cnpj/v1/${digits}`, mapBrasilApiCnpj)) ??
    (await consultaFonte(`https://publica.cnpj.ws/cnpj/${digits}`, mapCnpjaCnpj))
  );
}

/** Formata CPF (11 dígitos) ou CNPJ (14 dígitos) para exibição */
export function formatCpfCnpj(value: string): string {
  const n = (value || '').replace(/\D/g, '').slice(0, 14);
  if (n.length <= 3) return n;
  if (n.length <= 6) return n.slice(0, 3) + '.' + n.slice(3);
  if (n.length <= 9) return n.slice(0, 3) + '.' + n.slice(3, 6) + '.' + n.slice(6);
  if (n.length <= 11) return n.slice(0, 3) + '.' + n.slice(3, 6) + '.' + n.slice(6, 9) + '-' + n.slice(9);
  if (n.length <= 12) return n.slice(0, 2) + '.' + n.slice(2, 5) + '.' + n.slice(5, 8) + '/' + n.slice(8);
  return n.slice(0, 2) + '.' + n.slice(2, 5) + '.' + n.slice(5, 8) + '/' + n.slice(8, 12) + '-' + n.slice(12, 14);
}
