/**
 * Formatação de erros de formulário da API Clínica da Beleza (DRF).
 */

const PROCEDIMENTO_FIELD_LABELS: Record<string, string> = {
  name: 'Nome',
  description: 'Descrição',
  price: 'Preço',
  duration: 'Duração',
  category: 'Categoria',
};

const PACIENTE_FIELD_LABELS: Record<string, string> = {
  name: 'Nome',
  phone: 'Telefone',
  email: 'E-mail',
  cpf: 'CPF',
  birth_date: 'Data de Nascimento',
  address: 'Endereço',
  notes: 'Observações',
};

/** Erros 400 com rótulos amigáveis (pacientes, procedimentos e cadastros simples). */
export function formatClinicaApiValidationErrors(
  err: Record<string, unknown>,
  fieldLabels: Record<string, string> = PACIENTE_FIELD_LABELS,
): string {
  if (err?.detail && typeof err.detail === 'string') return err.detail;
  const msgs: string[] = [];
  for (const [key, val] of Object.entries(err)) {
    if (key === 'detail') continue;
    if (Array.isArray(val) && val.length && typeof val[0] === 'string') {
      msgs.push(`${fieldLabels[key] || key}: ${val[0]}`);
    } else if (typeof val === 'string' && val.trim()) {
      msgs.push(`${fieldLabels[key] || key}: ${val.trim()}`);
    }
  }
  return msgs.length ? msgs.join('. ') : '';
}

function appendEmailDuplicateHint(msg: string): string {
  if (msg.includes('Já existe') || msg.includes('já existe')) {
    return `${msg}\n\nSoluções:\n• Desmarque "Criar acesso" para cadastrar sem login\n• Use um email diferente\n• Ou use um e-mail que não esteja em uso no sistema`;
  }
  return msg;
}

/** Erros 400 de procedimentos. */
export function formatProcedimentoApiErrors(err: Record<string, unknown>): string {
  return formatClinicaApiValidationErrors(err, PROCEDIMENTO_FIELD_LABELS);
}

/** Erros da API de profissionais (inclui dicas para e-mail duplicado ao criar acesso). */
export function formatProfissionalApiErrors(err: Record<string, unknown>): string {
  const messages: string[] = [];
  if (typeof err.detail === 'string') messages.push(err.detail);
  else if (Array.isArray(err.detail)) messages.push(...(err.detail as string[]));

  for (const [key, v] of Object.entries(err)) {
    if (key === 'detail') continue;
    if (key === 'email' && Array.isArray(v)) {
      messages.push(...(v as string[]).map(appendEmailDuplicateHint));
    } else if (Array.isArray(v) && v.every((x) => typeof x === 'string')) {
      messages.push(...(v as string[]));
    } else if (typeof v === 'string' && v.trim()) {
      messages.push(key === 'email' ? appendEmailDuplicateHint(v.trim()) : v.trim());
    }
  }

  return messages.length ? messages.join('\n\n') : '';
}
