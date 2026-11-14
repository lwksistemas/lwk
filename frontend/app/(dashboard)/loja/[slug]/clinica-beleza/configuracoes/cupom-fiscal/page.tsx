"use client";

import { useParams } from "next/navigation";
import { Receipt } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { useClinicaBelezaTheme } from "@/components/clinica-beleza/ClinicaBelezaThemeContext";
import { CupomFiscalConfigForm } from "@/components/clinica-beleza/nfce/CupomFiscalConfigForm";

export default function ClinicaBelezaCupomFiscalPage() {
  const slug = (useParams()?.slug as string) ?? "";
  const base = `/loja/${slug}/clinica-beleza/configuracoes`;
  const { primary } = useClinicaBelezaTheme();

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Cupom fiscal"
        subtitle="NFC-e das vendas de produto"
        showOffline={false}
        icon={Receipt}
        backHref={base}
      />
      <ClinicaBelezaPageContent>
        <CupomFiscalConfigForm cor={primary} />
      </ClinicaBelezaPageContent>
    </>
  );
}
