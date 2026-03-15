/**
 * Utilitário para consulta de CEP (ViaCEP com fallback BrasilAPI).
 * Reutilizável em formulários de loja, lead, conta, etc.
 */

export interface EnderecoCep {
  logradouro: string;
  bairro: string;
  cidade: string;
  uf: string;
}

const TIMEOUT_MS = 10000;

function fetchWithTimeout(url: string): Promise<Response> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  return fetch(url, { signal: ctrl.signal }).finally(() => clearTimeout(t));
}

/**
 * Consulta CEP e retorna logradouro, bairro, cidade e UF.
 * @param cep - CEP com ou sem formatação (00000-000 ou 00000000)
 * @returns Dados do endereço ou null se não encontrado/erro
 */
export async function consultaCep(cep: string): Promise<EnderecoCep | null> {
  const digits = cep.replace(/\D/g, '');
  if (digits.length !== 8) return null;

  try {
    const resVia = await fetchWithTimeout(`https://viacep.com.br/ws/${digits}/json/`);
    if (resVia.ok) {
      const data = await resVia.json();
      if (data && !data.erro && data.cep) {
        return {
          logradouro: data.logradouro || '',
          bairro: data.bairro || '',
          cidade: data.localidade || '',
          uf: data.uf || '',
        };
      }
    }
  } catch {
    // Ignora e tenta BrasilAPI
  }

  try {
    const resBr = await fetchWithTimeout(`https://brasilapi.com.br/api/cep/v1/${digits}`);
    if (resBr.ok) {
      const data = await resBr.json();
      if (data && (data.street ?? data.city ?? data.state)) {
        return {
          logradouro: data.street || '',
          bairro: data.neighborhood || '',
          cidade: data.city || '',
          uf: data.state || '',
        };
      }
    }
  } catch {
    // Falha de rede ou timeout
  }

  return null;
}

/** Formata CEP para exibição (00000-000) */
export function formatarCep(cep: string): string {
  const digits = (cep || '').replace(/\D/g, '').slice(0, 8);
  if (digits.length >= 8) return `${digits.slice(0, 5)}-${digits.slice(5)}`;
  return digits;
}
