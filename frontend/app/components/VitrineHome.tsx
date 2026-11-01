import Link from "next/link";
import { SolicitacaoForm } from "@/components/site/SolicitacaoForm";
import type { PaginaHome, WhyUsBenefit } from "@/types/homepage";

const FAIXA = "w-full px-4 py-12 sm:px-6 lg:px-8";
const CARTAO = "rounded-2xl border border-cyan-300/50 bg-[#071833]/80 p-5 text-white shadow-[0_0_0_1px_rgba(34,211,238,0.08)]";
const BOTAO = "mt-5 inline-flex rounded-full bg-[#2f6bff] px-5 py-2.5 text-sm font-semibold text-white";

function Painel({ src, alt }: { src: string; alt: string }) {
  return (
    <picture>
      <source srcSet={src} type="image/webp" />
      <img src={src.replace(".webp", ".png")} alt={alt} width={1024} height={560} className="mt-5 h-auto w-full max-w-full rounded-xl border border-cyan-300/30" />
    </picture>
  );
}

function pagina(lista: PaginaHome[] | undefined, slug: string) {
  return lista?.find((item) => item.slug === slug);
}

function linhas(texto?: string) {
  return (texto || "").split("\n").map((linha) => linha.trim()).filter(Boolean);
}

function campo(paginaAtual: PaginaHome | undefined, chave: "titulo" | "resumo", padrao: string) {
  const valor = paginaAtual?.[chave]?.trim();
  return valor || padrao;
}

export default function VitrineHome({
  telefone,
  email,
  paginas,
  beneficios,
}: {
  telefone?: string;
  email?: string;
  paginas?: PaginaHome[];
  beneficios?: WhyUsBenefit[];
}) {
  const solucoes = pagina(paginas, "home-solucoes");
  const crm = pagina(paginas, "home-crm");
  const clinica = pagina(paginas, "home-clinica");
  const personalizados = pagina(paginas, "home-personalizados");
  const tituloBeneficios = pagina(paginas, "home-beneficios");
  const planos = pagina(paginas, "home-planos");
  const contato = pagina(paginas, "home-contato");

  const bulletsCrm = linhas(crm?.itens);
  const bulletsClinica = linhas(clinica?.itens);
  const cardsPersonalizados = linhas(personalizados?.itens).map((linha) => {
    const [titulo, texto] = linha.split("|");
    return { titulo: titulo.trim(), texto: (texto || "").trim() };
  }).filter((item) => item.titulo);
  const [botaoPersonalizado, linkPersonalizado] = (personalizados?.corpo || "Solicitar orçamento|/solucoes/personalizados").split("|");
  const cardsBeneficios = (beneficios || []).filter((item) => item.ativo !== false && item.titulo?.trim());
  const cardsPlanos = linhas(planos?.itens).map((linha) => {
    const [titulo, texto, href, botao] = linha.split("|");
    return {
      titulo: (titulo || "").trim(),
      texto: (texto || "").trim(),
      href: (href || "/contato").trim(),
      botao: (botao || "Saiba mais").trim(),
    };
  }).filter((item) => item.titulo);

  return (
    <div className="bg-[#031433] text-white">
      <section id="solucoes" className={`scroll-mt-24 ${FAIXA}`}>
        <h2 className="text-3xl font-bold tracking-tight">{campo(solucoes, "titulo", "Nossas soluções")}</h2>
        <p className="mt-3 max-w-3xl text-lg text-slate-200">
          {campo(solucoes, "resumo", "Dois sistemas prontos. O detalhe de cada um fica na página do produto.")}
        </p>
        <div className="mt-8 grid gap-4 lg:grid-cols-2">
          <article className={`${CARTAO} min-w-0`}>
            <h3 className="text-2xl font-bold">{campo(crm, "titulo", "LWK Sales Cloud — CRM de Vendas")}</h3>
            <p className="mt-2 text-slate-300">{campo(crm, "resumo", "Para equipes comerciais acompanharem o cliente do primeiro contato ao fechamento.")}</p>
            <ul className="mt-4 space-y-2 text-slate-100">
              {(bulletsCrm.length ? bulletsCrm : ["Leads e funil no mesmo lugar", "Propostas e contratos em andamento", "Relatórios do comercial"]).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <Painel src="/homepage/crm-tela.webp" alt="Painel do CRM de Vendas" />
            <Link href="/solucoes/crm-vendas" className={BOTAO}>Conhecer o CRM</Link>
          </article>
          <article className={`${CARTAO} min-w-0`}>
            <h3 className="text-2xl font-bold">{campo(clinica, "titulo", "Gestão para Clínicas de Estética")}</h3>
            <p className="mt-2 text-slate-300">{campo(clinica, "resumo", "Para a rotina da clínica: quem chega, o que foi feito e como está o dia.")}</p>
            <ul className="mt-4 space-y-2 text-slate-100">
              {(bulletsClinica.length ? bulletsClinica : ["Agenda do dia", "Procedimentos e protocolos", "Estoque e financeiro da clínica"]).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <Painel src="/homepage/clinica-tela.webp" alt="Painel da gestão para clínicas de estética" />
            <Link href="/solucoes/clinicas-estetica" className={BOTAO}>Conhecer o sistema</Link>
          </article>
        </div>
      </section>

      <section id="personalizados" className={`scroll-mt-24 border-t border-white/10 bg-[#04183f] ${FAIXA}`}>
        <h2 className="text-3xl font-bold tracking-tight">{campo(personalizados, "titulo", "Desenvolvimento de sistemas personalizados")}</h2>
        <p className="mt-3 max-w-3xl text-lg text-slate-200">
          {campo(personalizados, "resumo", "Quando a operação não cabe no CRM nem na clínica, a LWK desenvolve o software sob medida. Não há sistema pronto para outros segmentos.")}
        </p>
        <ul className="mt-8 grid gap-4 sm:grid-cols-3">
          {(cardsPersonalizados.length ? cardsPersonalizados : [
            { titulo: "A operação primeiro", texto: "O levantamento parte da rotina real da empresa." },
            { titulo: "Feito para o processo", texto: "Telas e regras do jeito que a equipe trabalha." },
            { titulo: "Depois da entrega", texto: "Suporte para o sistema continuar em uso." },
          ]).map((item) => (
            <li key={item.titulo} className={CARTAO}>
              <p className="font-semibold">{item.titulo}</p>
              <p className="mt-2 text-sm leading-relaxed text-slate-300">{item.texto}</p>
            </li>
          ))}
        </ul>
        <Link href={(linkPersonalizado || "/solucoes/personalizados").trim()} className="mt-8 inline-flex rounded-full bg-[#2f6bff] px-5 py-2.5 text-sm font-semibold text-white">
          {(botaoPersonalizado || "Solicitar orçamento").trim()}
        </Link>
      </section>

      <section id="beneficios" className={`scroll-mt-24 border-t border-white/10 ${FAIXA}`}>
        <h2 className="text-3xl font-bold tracking-tight">{campo(tituloBeneficios, "titulo", "Benefícios e diferenciais")}</h2>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {(cardsBeneficios.length ? cardsBeneficios.map((item) => ({ titulo: item.titulo, texto: item.descricao })) : [
            { titulo: "Tecnologia e segurança", texto: "Sistemas feitos para o uso diário, com cuidado sobre os dados." },
            { titulo: "Suporte especializado", texto: "Quem atende conhece o produto que a empresa contratou." },
            { titulo: "Na nuvem", texto: "A equipe acessa de onde estiver, no computador ou no celular." },
            { titulo: "Sob medida quando precisa", texto: "O pronto cobre clínica e comercial. O resto vira projeto." },
          ]).map((item) => (
            <article key={item.titulo} className={CARTAO}>
              <h3 className="text-lg font-semibold">{item.titulo}</h3>
              {item.texto ? <p className="mt-2 text-sm leading-relaxed text-slate-300">{item.texto}</p> : null}
            </article>
          ))}
        </div>
      </section>

      <section id="planos" className={`scroll-mt-24 border-t border-white/10 bg-[#04183f] ${FAIXA}`}>
        <h2 className="text-3xl font-bold tracking-tight">{campo(planos, "titulo", "Planos e proposta")}</h2>
        <p className="mt-3 max-w-3xl text-lg text-slate-200">
          {campo(planos, "resumo", "Os valores publicados são os da gestão para clínicas. CRM e sistemas personalizados seguem sob consulta.")}
        </p>
        <div className="mt-8 grid gap-4 lg:grid-cols-3">
          {(cardsPlanos.length ? cardsPlanos : [
            { titulo: "Gestão para clínicas", texto: "Planos com valores publicados, a partir de R$ 99,90 por mês.", href: "/planos", botao: "Ver planos" },
            { titulo: "CRM de Vendas", texto: "Consulte nossas condições comerciais.", href: "/contato", botao: "Solicitar proposta" },
            { titulo: "Sistema personalizado", texto: "O valor depende do que a operação precisa.", href: "/solucoes/personalizados", botao: "Pedir orçamento" },
          ]).map((item) => (
            <article key={item.titulo} className={CARTAO}>
              <h3 className="text-xl font-bold">{item.titulo}</h3>
              <p className="mt-2 text-slate-300">{item.texto}</p>
              <Link href={item.href} className={BOTAO}>{item.botao}</Link>
            </article>
          ))}
        </div>
      </section>

      <section id="pedir-demonstracao" className={`scroll-mt-24 border-t border-white/10 bg-[#04183f] ${FAIXA}`}>
        <h2 className="text-3xl font-bold tracking-tight">{campo(contato, "titulo", "Contato e demonstração")}</h2>
        <p className="mt-3 max-w-3xl text-lg text-slate-200">
          {campo(contato, "resumo", "Escolha o CRM, a clínica ou um sistema personalizado. A mensagem do WhatsApp já leva o produto, o nome e a empresa.")}
        </p>
        {(telefone || email) && (
          <p className="mt-4 text-slate-300">
            {email}
            {email && telefone ? " · " : ""}
            {telefone ? `WhatsApp ${telefone}` : ""}
          </p>
        )}
        <div className="mt-8 rounded-2xl border border-cyan-300/30 bg-white p-5 text-slate-900 sm:p-6">
          <SolicitacaoForm origem="demonstracao" telefone={telefone} />
        </div>
      </section>
    </div>
  );
}
