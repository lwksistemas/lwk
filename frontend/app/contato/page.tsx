import type { Metadata } from "next";
import { ConteudoPagina } from "@/components/site/ConteudoPagina";
import { SiteShell } from "@/components/site/SiteShell";
import { SolicitacaoForm } from "@/components/site/SolicitacaoForm";
import { carregarHome, carregarPagina } from "@/lib/site";

export const metadata: Metadata = {
  title: "Contato | LWK Sistemas",
  description: "Fale com a LWK Sistemas por formulário, telefone ou WhatsApp.",
};

export default async function ContatoPage() {
  const [home, pagina, crm, clinica, personalizado] = await Promise.all([
    carregarHome(),
    carregarPagina("contato"),
    carregarPagina("crm-vendas"),
    carregarPagina("clinicas-estetica"),
    carregarPagina("personalizados"),
  ]);
  const empresa = home.empresa;

  return (
    <SiteShell data={home}>
      <ConteudoPagina pagina={pagina} telefone={empresa?.telefone_whatsapp}>
        <div className="mb-8 space-y-1 text-sm text-slate-700">
          {empresa?.telefone_whatsapp && <p>WhatsApp: {empresa.telefone_whatsapp}</p>}
          {empresa?.email_contato && <p>E-mail: {empresa.email_contato}</p>}
          {empresa?.endereco && <p>{empresa.endereco}</p>}
        </div>
        <SolicitacaoForm
          origem="contato"
          produtoInicial="outros"
          telefone={empresa?.telefone_whatsapp}
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
