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

export function filterPatientsLocal(
  patients: PatientQuickOption[],
  searchQuery: string,
  limit = 40,
): PatientQuickOption[] {
  return patients.filter((p) => matchesPatientSearchQuery(p, searchQuery)).slice(0, limit);
}
