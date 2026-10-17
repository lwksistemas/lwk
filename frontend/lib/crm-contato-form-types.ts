export interface CrmContatoFormData {
  nome: string;
  email: string;
  telefone: string;
  cargo: string;
  conta: string;
  observacoes: string;
}

export const EMPTY_CONTATO_FORM: CrmContatoFormData = {
  nome: '',
  email: '',
  telefone: '',
  cargo: '',
  conta: '',
  observacoes: '',
};

/** Copia telefone e e-mail da conta. Campo vazio na empresa não apaga o que já foi digitado. */
export function aplicarDadosEmpresaNoContato(
  form: CrmContatoFormData,
  conta: { telefone?: string | null; email?: string | null },
): CrmContatoFormData | null {
  const telefone = (conta.telefone || '').trim();
  const email = (conta.email || '').trim();
  if (!telefone && !email) return null;
  return {
    ...form,
    telefone: telefone || form.telefone,
    email: email || form.email,
  };
}
