/**
 * Consulta CNPJ via BrasilAPI para preencher dados da empresa automaticamente.
 * Reutilizável em formulários de lead, conta, etc.
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
  optante_simples?: boolean;
}

const TIMEOUT_MS = 15000;

function fetchWithTimeout(url: string): Promise<Response> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  return fetch(url, { signal: ctrl.signal }).finally(() => clearTimeout(t));
}

/**
 * Consulta CNPJ na BrasilAPI e retorna dados da empresa.
 * @param cnpj - CNPJ com ou sem formatação (00.000.000/0001-00 ou 00000000000100)
 * @returns Dados da empresa ou null se não encontrado/erro
 */
export async function consultaCnpj(cnpj: string): Promise<DadosCnpj | null> {
  const digits = cnpj.replace(/\D/g, '');
  if (digits.length !== 14) return null;

  try {
    const res = await fetchWithTimeout(`https://brasilapi.com.br/api/cnpj/v1/${digits}`);
    if (!res.ok) return null;
    const data = await res.json();
    if (!data) return null;

    const formatCepFromApi = (v: string | number | null | undefined) => {
      const raw = v == null ? '' : String(v);
      const n = raw.replace(/\D/g, '');
      if (!n) return '';
      const padded = n.length < 8 ? n.padStart(8, '0') : n.slice(0, 8);
      return padded.slice(0, 5) + '-' + padded.slice(5, 8);
    };

    const ibge = data.codigo_municipio_ibge ?? data.codigo_municipio;
    const cnae = data.cnae_fiscal;
    return {
      razao_social: data.razao_social || data.nome_fantasia || '',
      nome_fantasia: data.nome_fantasia || undefined,
      cep: formatCepFromApi(data.cep) || '',
      logradouro: data.logradouro || '',
      numero: data.numero || '',
      complemento: data.complemento || '',
      bairro: data.bairro || '',
      municipio: data.municipio || '',
      uf: data.uf || '',
      codigo_municipio_ibge: ibge != null ? String(ibge).replace(/\D/g, '').slice(0, 7) : undefined,
      cnae_fiscal: cnae != null ? String(cnae).replace(/\D/g, '') : undefined,
      email: (data.email || data.correio_eletronico || '').trim() || undefined,
      optante_simples: typeof data.opcao_pelo_simples === 'boolean' ? data.opcao_pelo_simples : undefined,
    };
  } catch {
    return null;
  }
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
