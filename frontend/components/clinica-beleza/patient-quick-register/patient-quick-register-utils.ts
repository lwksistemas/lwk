import type { PatientQuickOption } from "./patient-quick-register-types";
import { matchesPatientSearchQuery } from "@/lib/clinica-beleza-entities";

export function buildPatientQuickSearchQuery(nome: string, telefone: string, cpf: string): string {
  const cpfDigits = cpf.replace(/\D/g, "");
  const telDigits = telefone.replace(/\D/g, "");
  const nomeTrim = nome.trim();
  if (cpfDigits.length >= 3) return cpfDigits;
  if (telDigits.length >= 3) return telDigits;
  if (nomeTrim.length >= 1) return nomeTrim;
  return "";
}

/** Campo único do modal de agenda: dígitos → CPF/tel; senão nome. */
export function buildAgendaPatientSearchQuery(busca: string): string {
  const t = (busca || "").trim();
  if (!t) return "";
  const compact = t.replace(/\s/g, "");
  const digits = compact.replace(/\D/g, "");
  if (digits.length >= 3 && digits.length >= Math.ceil(compact.length * 0.6)) return digits;
  return t;
}

export function filterPatientsLocal(
  patients: PatientQuickOption[],
  searchQuery: string,
  limit = 40,
): PatientQuickOption[] {
  return patients.filter((p) => matchesPatientSearchQuery(p, searchQuery)).slice(0, limit);
}
