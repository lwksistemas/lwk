"use client";

import { useParams } from "next/navigation";
import { Phone } from "lucide-react";
import { ClinicaBelezaPageContent } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ClinicaBelezaStandardPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { useClinicaBelezaTheme } from "@/components/clinica-beleza/ClinicaBelezaThemeContext";
import { ContatoReciboSettings } from "@/components/loja/ContatoReciboSettings";

export default function ClinicaBelezaContatoReciboPage() {
  const slug = (useParams()?.slug as string) ?? "";
  const base = `/loja/${slug}/clinica-beleza/configuracoes`;
  const { primary } = useClinicaBelezaTheme();

  return (
    <>
      <ClinicaBelezaStandardPageHeader
        title="Contato no recibo"
        subtitle="Telefone e e-mail da clínica no recibo de pagamento"
        showOffline={false}
        icon={Phone}
        backHref={base}
      />
      <ClinicaBelezaPageContent>
        <ContatoReciboSettings
          apiPrefix="/clinica-beleza"
          accentColor={primary}
          entidadeLabel="clínica"
        />
      </ClinicaBelezaPageContent>
    </>
  );
}
