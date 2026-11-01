import type { Metadata } from "next";
import Modules from "@/app/components/Modules";
import { ConteudoPagina } from "@/components/site/ConteudoPagina";
import { SiteShell } from "@/components/site/SiteShell";
import { carregarHome, carregarPagina } from "@/lib/site";

export const metadata: Metadata = {
  title: "Planos | LWK Sistemas",
  description: "Planos e valores dos sistemas LWK.",
};

export default async function PlanosPage() {
  const [home, pagina] = await Promise.all([carregarHome(), carregarPagina("planos")]);
  return (
    <SiteShell data={home}>
      <ConteudoPagina pagina={pagina} telefone={home.empresa?.telefone_whatsapp} />
      <Modules modulos={home.modulos ?? []} />
    </SiteShell>
  );
}
