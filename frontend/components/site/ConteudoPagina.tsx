import Link from "next/link";
import type { PaginaConteudo } from "@/lib/site";
import { linkWhatsapp } from "@/lib/site";

const IMAGENS: Record<string, { src: string; alt: string }> = {
  "crm-vendas": {
    src: "/homepage/crm-tela.webp",
    alt: "Painel do LWK Sales Cloud com receita, leads, pipeline e funil.",
  },
  "clinicas-estetica": {
    src: "/homepage/clinica-tela.webp",
    alt: "Painel da gestão para clínicas de estética com a agenda do dia.",
  },
};

export function ConteudoPagina({
  pagina,
  telefone,
  children,
}: {
  pagina: PaginaConteudo;
  telefone?: string;
  children?: React.ReactNode;
}) {
  const itens = pagina.itens.split("\n").map((item) => item.trim()).filter(Boolean);
  const whatsapp = linkWhatsapp(telefone, pagina.mensagem_whatsapp);
  const imagem = IMAGENS[pagina.slug];
  const demonstracao = `/demonstracao?produto=${pagina.slug}`;
  const acao =
    pagina.slug === "planos"
      ? { href: "/contato", rotulo: "Solicitar proposta", externo: false }
      : pagina.slug === "segmentos"
        ? { href: whatsapp || "/contato", rotulo: "Converse com nossa equipe", externo: Boolean(whatsapp) }
        : pagina.slug === "personalizados"
          ? null
          : children
            ? null
            : { href: demonstracao, rotulo: "Solicitar demonstração", externo: false };
  const rotuloWhatsapp = pagina.slug === "planos" ? "Falar com consultor" : "WhatsApp deste produto";

  return (
    <article className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <p className="text-sm font-medium text-blue-700">LWK Sistemas</p>
      <h1 className="mt-2 text-3xl font-bold text-slate-900 sm:text-4xl">{pagina.titulo}</h1>
      {pagina.resumo && <p className="mt-4 text-lg text-slate-600">{pagina.resumo}</p>}
      {imagem && (
        <picture>
          <source srcSet={imagem.src} type="image/webp" />
          <img
            src={imagem.src.replace(".webp", ".png")}
            alt={imagem.alt}
            width={1024}
            height={560}
            className="mt-6 w-full rounded-xl border border-slate-200 bg-slate-50"
          />
        </picture>
      )}
      {pagina.corpo && <p className="mt-4 leading-relaxed text-slate-700">{pagina.corpo}</p>}
      {pagina.slug === "planos" && (
        <p className="mt-4 leading-relaxed text-slate-700">
          Os valores publicados são os da gestão para clínicas. Para o CRM de Vendas e os sistemas personalizados, consulte nossas condições comerciais.
        </p>
      )}
      {itens.length > 0 && (
        <ul className="mt-6 grid gap-2 sm:grid-cols-2">
          {itens.map((item) => (
            <li key={item} className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-800">
              {item}
            </li>
          ))}
        </ul>
      )}
      <div className="mt-8 flex flex-wrap gap-3">
        {acao && (
          acao.externo ? (
            <a href={acao.href} target="_blank" rel="noopener noreferrer" className="rounded-full bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white">
              {acao.rotulo}
            </a>
          ) : (
            <Link href={acao.href} className="rounded-full bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white">
              {acao.rotulo}
            </Link>
          )
        )}
        {whatsapp && pagina.slug !== "segmentos" && (
          <a href={whatsapp} target="_blank" rel="noopener noreferrer" className="rounded-full border border-green-600 px-5 py-2.5 text-sm font-semibold text-green-700">
            {rotuloWhatsapp}
          </a>
        )}
      </div>
      {children && <div className="mt-10">{children}</div>}
    </article>
  );
}
