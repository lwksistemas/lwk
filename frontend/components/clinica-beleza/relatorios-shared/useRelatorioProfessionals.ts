import { useEffect, useState } from "react";
import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import type { RelatorioProfessionalOption } from "./relatorios-shared-utils";

export function useRelatorioProfessionals() {
  const [professionals, setProfessionals] = useState<RelatorioProfessionalOption[]>([]);

  useEffect(() => {
    clinicaBelezaFetch("/professionals/")
      .then(async (res) => {
        if (res.ok) {
          const json = await res.json();
          setProfessionals(json.results || json);
        }
      })
      .catch(() => {});
  }, []);

  return professionals;
}
