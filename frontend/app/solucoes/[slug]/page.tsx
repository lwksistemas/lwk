import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ConteudoPagina } from "@/components/site/ConteudoPagina";
import { SiteShell } from "@/components/site/SiteShell";
import { SolicitacaoForm } from "@/components/site/SolicitacaoForm";
import { carregarHome, carregarPagina } from "@/lib/site";

const SLUGS = ["crm-vendas", "clinicas-estetica", "personalizados"] as const;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  if (!SLUGS.includes(slug as (typeof SLUGS)[number])) return { title: "LWK Sistemas" };
  const pagina = await carregarPagina(slug);
  return {
    title: `${pagina.titulo} | LWK Sistemas`,
    description: pagina.resumo,
  };
}

export default async function PaginaSolucao({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  if (!SLUGS.includes(slug as (typeof SLUGS)[number])) notFound();
  const [home, pagina] = await Promise.all([carregarHome(), carregarPagina(slug)]);
  return (
    <SiteShell data={home}>
      <ConteudoPagina pagina={pagina} telefone={home.empresa?.telefone_whatsapp}>
        {slug === "personalizados" && (
          <SolicitacaoForm origem="orcamento" produtoInicial="personalizados" telefone={home.empresa?.telefone_whatsapp} />
        )}
      </ConteudoPagina>
    </SiteShell>
  );
}
