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
    <article className="w-full px-4 py-12 text-white sm:px-6 lg:px-8">
      <p className="text-sm font-medium text-sky-300">LWK Sistemas</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">{pagina.titulo}</h1>
      {pagina.resumo && <p className="mt-4 max-w-3xl text-lg text-slate-200">{pagina.resumo}</p>}
      {imagem && (
        <picture>
          <source srcSet={imagem.src} type="image/webp" />
          <img
            src={imagem.src.replace(".webp", ".png")}
            alt={imagem.alt}
            width={1024}
            height={560}
            className="mt-6 h-auto w-full max-w-full rounded-xl border border-cyan-300/30"
          />
        </picture>
      )}
      {pagina.corpo && <p className="mt-4 max-w-3xl leading-relaxed text-slate-200">{pagina.corpo}</p>}
      {itens.length > 0 && (
        <ul className="mt-6 grid gap-3 sm:grid-cols-2">
          {itens.map((item) => (
            <li key={item} className="rounded-2xl border border-cyan-300/40 bg-[#071833]/80 px-4 py-3 text-sm font-medium text-white">
              {item}
            </li>
          ))}
        </ul>
      )}
      <div className="mt-8 flex flex-wrap gap-3">
        {acao && (
          acao.externo ? (
            <a href={acao.href} target="_blank" rel="noopener noreferrer" className="rounded-full bg-[#2f6bff] px-5 py-2.5 text-sm font-semibold text-white">
              {acao.rotulo}
            </a>
          ) : (
            <Link href={acao.href} className="rounded-full bg-[#2f6bff] px-5 py-2.5 text-sm font-semibold text-white">
              {acao.rotulo}
            </Link>
          )
        )}
        {whatsapp && pagina.slug !== "segmentos" && (
          <a href={whatsapp} target="_blank" rel="noopener noreferrer" className="rounded-full border border-white/40 px-5 py-2.5 text-sm font-semibold text-white">
            {rotuloWhatsapp}
          </a>
        )}
      </div>
      {children && (
        <div className="mt-10 rounded-2xl border border-cyan-300/30 bg-white p-5 text-slate-900 sm:p-6">
          {children}
        </div>
      )}
    </article>
  );
}
