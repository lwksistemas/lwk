import type { Metadata } from "next";
import { SiteShell } from "@/components/site/SiteShell";
import { carregarHome } from "@/lib/site";

export const metadata: Metadata = {
  title: "Política de Privacidade | LWK Sistemas",
  description: "Como a LWK Sistemas usa os dados enviados pelo site.",
};

export default async function PrivacidadePage() {
  const home = await carregarHome();
  const email = home.empresa?.email_contato;

  return (
    <SiteShell data={home}>
      <article className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
        <p className="text-sm font-medium text-blue-700">LWK Sistemas</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-900">Política de Privacidade</h1>
        <div className="mt-6 space-y-4 leading-relaxed text-slate-700">
          <p>
            Os formulários do site pedem nome, empresa ou clínica, WhatsApp, produto de interesse e a mensagem do contato. No orçamento de sistema personalizado, também pedimos o segmento e a descrição do que precisa ser desenvolvido.
          </p>
          <p>
            Esses dados servem só para a equipe comercial retornar o pedido de demonstração, proposta ou orçamento. A LWK não vende essa lista e não usa o formulário para outra finalidade.
          </p>
          <p>
            As imagens públicas dos sistemas são de demonstração, sem nomes de clientes, pacientes ou dados comerciais identificáveis.
          </p>
          <p>
            Para pedir a correção ou a exclusão de um contato enviado pelo site, escreva para {email || "o e-mail comercial informado na página de contato"}.
          </p>
        </div>
      </article>
    </SiteShell>
  );
}
