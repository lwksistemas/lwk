import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { apenasDigitos } from "@/lib/format-br";
import { toBrDateMemed } from "@/lib/memed-prescricao-parser";
import { enviarComandoPrescricaoMemed } from "./memed-script-loader";

export interface DadosClinicaMemed {
  local_name?: string;
  address?: string;
  city?: string;
  state?: string;
  phone?: string;
}

/**
 * True se o CPF do paciente também é de um prescritor na Memed (conflito que faz
 * o editor quebrar ao gerar a receita). Best-effort: qualquer falha retorna false
 * (não impede a prescrição).
 */
async function cpfPacienteConflitaComPrescritor(cpf: string): Promise<boolean> {
  try {
    const r = await ClinicaBelezaAPI.memed.verificarCpfPaciente(cpf);
    return Boolean(r?.conflito_prescritor);
  } catch {
    return false;
  }
}

export async function montarPacienteMemed(
  patientId: number,
  patientName: string,
): Promise<Record<string, unknown>> {
  let detalhe: Record<string, unknown> = {};
  try {
    detalhe = await ClinicaBelezaAPI.get(`/patients/${patientId}/`);
  } catch {
    // prescritor completa na Memed
  }

  const paciente: Record<string, unknown> = {
    idExterno: String(patientId),
    external_id: String(patientId),
    nome: detalhe?.nome || patientName,
  };
  const cpf = apenasDigitos(String(detalhe?.cpf ?? ""));
  // Se o CPF do paciente também for de um PRESCRITOR na Memed, enviar esse CPF
  // faz o editor quebrar ao gerar a receita (verifyIdentifyDataToNavigate:
  // "Cannot read properties of undefined (reading 'attributes')"). Nesse caso
  // omitimos o CPF do paciente — a receita é gerada normalmente, só sem o
  // preenchimento automático a partir do CPF.
  if (cpf && !(await cpfPacienteConflitaComPrescritor(cpf))) {
    paciente.cpf = cpf;
  }
  const telefone = apenasDigitos(String(detalhe?.telefone ?? ""));
  if (telefone) paciente.telefone = telefone;
  if (detalhe?.email) paciente.email = detalhe.email;
  if (detalhe?.endereco) paciente.endereco = detalhe.endereco;
  if (detalhe?.cidade) paciente.cidade = detalhe.cidade;
  const dataNascimento = toBrDateMemed(detalhe?.data_nascimento as string | null);
  if (dataNascimento) paciente.data_nascimento = dataNascimento;

  return paciente;
}

export async function enviarPacienteMemed(patientId: number, patientName: string): Promise<void> {
  const paciente = await montarPacienteMemed(patientId, patientName);
  await enviarComandoPrescricaoMemed("setPaciente", paciente);
}

export async function enviarWorkplaceMemed(clinica: DadosClinicaMemed | null): Promise<void> {
  if (!clinica?.local_name) return;
  const workplace: Record<string, unknown> = { local_name: clinica.local_name };
  if (clinica.address) workplace.address = clinica.address;
  if (clinica.city) workplace.city = clinica.city;
  if (clinica.state) workplace.state = clinica.state;
  if (clinica.phone) workplace.phone = String(clinica.phone);
  await enviarComandoPrescricaoMemed("setWorkplace", workplace);
}
