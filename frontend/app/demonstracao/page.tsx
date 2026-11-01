import type { Metadata } from "next";
import { ConteudoPagina } from "@/components/site/ConteudoPagina";
import { SiteShell } from "@/components/site/SiteShell";
import { SolicitacaoForm } from "@/components/site/SolicitacaoForm";
import { carregarHome, carregarPagina } from "@/lib/site";

export const metadata: Metadata = {
  title: "Solicitar demonstração | LWK Sistemas",
  description: "Escolha o CRM Vendas, a gestão para clínicas ou um sistema personalizado e peça uma apresentação.",
};

export default async function DemonstracaoPage({
  searchParams,
}: {
  searchParams: Promise<{ produto?: string }>;
}) {
  const { produto } = await searchParams;
  const [home, pagina, crm, clinica, personalizado] = await Promise.all([
    carregarHome(),
    carregarPagina("demonstracao"),
    carregarPagina("crm-vendas"),
    carregarPagina("clinicas-estetica"),
    carregarPagina("personalizados"),
  ]);

  return (
    <SiteShell data={home}>
      <ConteudoPagina pagina={pagina} telefone={home.empresa?.telefone_whatsapp}>
        <SolicitacaoForm
          origem="demonstracao"
          produtoInicial={produto}
          telefone={home.empresa?.telefone_whatsapp}
          mensagens={{
            "crm-vendas": crm.mensagem_whatsapp,
            "clinicas-estetica": clinica.mensagem_whatsapp,
            personalizados: personalizado.mensagem_whatsapp,
            outros: pagina.mensagem_whatsapp,
            geral: pagina.mensagem_whatsapp,
          }}
        />
      </ConteudoPagina>
    </SiteShell>
  );
}
