/**
 * Busca do tomador e padrões de serviço da nota da clínica.
 * Não consulta cliente, lead nem template do CRM.
 */
import apiClient from '@/lib/api-client';
import { ensureArray } from '@/lib/array-helpers';
import { consultaCnpj } from '@/lib/consulta-cnpj';

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
  item_lista_servico: '',
  codigo_tributacao_nacional: '',
};

export type NfseDefaultsServico = {
  servico_descricao: string;
  codigo_cnae: string;
  codigo_servico: string;
  item_lista_servico: string;
  codigo_tributacao_nacional: string;
};

export type NfseEmissaoContaOption = {
  id: number | string;
  _tipo: 'conta' | 'lead';
  _fonte?: 'conta' | 'lead' | 'nfse' | 'brasilapi' | 'paciente';
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
  _display?: string;
};

export function somenteDigitosDocumento(value: string): string {
  return (value || '').replace(/\D/g, '');
}

export function preencherFormTomador(
  conta: NfseEmissaoContaOption,
): Partial<typeof NFSE_EMISSAO_INITIAL_FORM> {
  return {
    conta_id: null,
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

export function defaultsServicoClinica(
  config: {
    descricao_servico_padrao?: string;
    codigo_servico_municipal?: string;
    codigo_cnae?: string;
    item_lista_servico?: string;
    codigo_tributacao_nacional?: string;
    codigo_tributacao_municipal?: string;
  } | null,
  descricaoOverride?: string,
): NfseDefaultsServico {
  const descricao = (descricaoOverride || '').trim() || config?.descricao_servico_padrao || '';
  return {
    servico_descricao: descricao,
    codigo_servico: config?.codigo_tributacao_municipal || config?.codigo_servico_municipal || '',
    codigo_cnae: config?.codigo_cnae || '',
    item_lista_servico: config?.item_lista_servico || '',
    codigo_tributacao_nacional: config?.codigo_tributacao_nacional || '',
  };
}

function tomadorDaResposta(d: Record<string, unknown>, documento: string, digits: string): NfseEmissaoContaOption {
  const fonte = String(d.fonte || 'paciente');
  return {
    id: (d.conta_id as number | undefined) ?? `${fonte}_${digits}`,
    _tipo: 'lead',
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

async function buscarPacienteClinica(documento: string, digits: string): Promise<NfseEmissaoContaOption | null> {
  try {
    const res = await apiClient.get('/clinica-beleza/patients/', {
      params: { search: digits, page_size: 15 },
    });
    const lista = ensureArray<Record<string, unknown>>(res.data);
    const paciente = lista.find((p) => somenteDigitosDocumento(String(p.cpf || '')) === digits);
    if (!paciente) return null;
    return tomadorDaResposta(
      {
        fonte: 'paciente',
        nome: paciente.nome || paciente.name,
        cpf_cnpj: paciente.cpf || documento,
        email: paciente.email,
        logradouro: paciente.endereco || paciente.address,
        numero: 'S/N',
        cidade: paciente.cidade,
        uf: paciente.estado || paciente.uf,
      },
      documento,
      digits,
    );
  } catch {
    return null;
  }
}

/** Paciente da clínica, nota já emitida nesta loja ou Receita Federal (CNPJ). */
export async function buscarTomadorClinicaPorDocumento(
  documento: string,
): Promise<NfseEmissaoContaOption | null> {
  const digits = somenteDigitosDocumento(documento);
  if (digits.length !== 11 && digits.length !== 14) return null;

  const paciente = await buscarPacienteClinica(documento, digits);
  if (paciente) return paciente;

  try {
    const res = await apiClient.get('/nfse/buscar-tomador/', { params: { documento: digits } });
    const d = res.data as Record<string, unknown>;
    if (d?.encontrado && d.fonte !== 'conta' && d.fonte !== 'lead') {
      return tomadorDaResposta(d, documento, digits);
    }
  } catch {
    // segue para nota anterior ou Receita
  }

  try {
    const res = await apiClient.get('/nfse/', { params: { busca: digits } });
    const lista = ensureArray<Record<string, unknown>>(res.data);
    const nf = lista.find(
      (item) => somenteDigitosDocumento(String(item.tomador_cpf_cnpj || '')) === digits && item.tomador_nome,
    );
    if (nf) {
      return tomadorDaResposta(
        {
          fonte: 'nfse',
          nome: nf.tomador_nome,
          cpf_cnpj: nf.tomador_cpf_cnpj || documento,
          email: nf.tomador_email,
        },
        documento,
        digits,
      );
    }
  } catch {
    // segue para CNPJ na Receita
  }

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
