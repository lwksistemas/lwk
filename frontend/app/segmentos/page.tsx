import type { Metadata } from "next";
import { ConteudoPagina } from "@/components/site/ConteudoPagina";
import { SiteShell } from "@/components/site/SiteShell";
import { carregarHome, carregarPagina } from "@/lib/site";

export const metadata: Metadata = {
  title: "Segmentos | LWK Sistemas",
  description: "Clínicas de estética, equipes comerciais e projetos para outros segmentos.",
};

export default async function SegmentosPage() {
  const [home, pagina] = await Promise.all([carregarHome(), carregarPagina("segmentos")]);
  return (
    <SiteShell data={home}>
      <ConteudoPagina pagina={pagina} telefone={home.empresa?.telefone_whatsapp} />
    </SiteShell>
  );
}
