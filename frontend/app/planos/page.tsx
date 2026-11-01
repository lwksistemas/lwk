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
  const conteudo = {
    ...pagina,
    resumo: "Os valores publicados são os da gestão para clínicas. CRM e sistemas personalizados seguem sob consulta.",
    corpo: "Cada tipo tem a sua condição. A clínica tem três planos. O CRM e o sistema personalizado são orçados à parte.",
  };
  return (
    <SiteShell data={home}>
      <ConteudoPagina pagina={conteudo} telefone={home.empresa?.telefone_whatsapp} />
      <Modules />
    </SiteShell>
  );
}
