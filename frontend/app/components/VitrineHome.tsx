import Link from "next/link";
import { SolicitacaoForm } from "@/components/site/SolicitacaoForm";

const FAIXA = "w-full px-4 py-12 sm:px-6 lg:px-8";
const CARTAO = "rounded-2xl border border-cyan-300/50 bg-[#071833]/80 p-5 text-white shadow-[0_0_0_1px_rgba(34,211,238,0.08)]";

function Painel({ src, alt }: { src: string; alt: string }) {
  return (
    <picture>
      <source srcSet={src} type="image/webp" />
      <img src={src.replace(".webp", ".png")} alt={alt} width={1024} height={560} className="mt-5 h-auto w-full max-w-full rounded-xl border border-cyan-300/30" />
    </picture>
  );
}

export default function VitrineHome({
  telefone,
  email,
}: {
  telefone?: string;
  email?: string;
}) {
  return (
    <div className="bg-[#031433] text-white">
      <section id="solucoes" className={`scroll-mt-24 ${FAIXA}`}>
        <h2 className="text-3xl font-bold tracking-tight">Nossas soluções</h2>
        <p className="mt-3 max-w-3xl text-lg text-slate-200">
          Dois sistemas prontos. O detalhe de cada um fica na página do produto.
        </p>
        <div className="mt-8 grid gap-4 lg:grid-cols-2">
          <article className={`${CARTAO} min-w-0`}>
            <h3 className="text-2xl font-bold">LWK Sales Cloud — CRM de Vendas</h3>
            <p className="mt-2 text-slate-300">Para equipes comerciais acompanharem o cliente do primeiro contato ao fechamento.</p>
            <ul className="mt-4 space-y-2 text-slate-100">
              <li>Leads e funil no mesmo lugar</li>
              <li>Propostas e contratos em andamento</li>
              <li>Relatórios do comercial</li>
            </ul>
            <Painel src="/homepage/crm-tela.webp" alt="Painel do CRM de Vendas" />
            <Link href="/solucoes/crm-vendas" className="mt-5 inline-flex rounded-full bg-[#2f6bff] px-5 py-2.5 text-sm font-semibold text-white">
              Conhecer o CRM
            </Link>
          </article>
          <article className={`${CARTAO} min-w-0`}>
            <h3 className="text-2xl font-bold">Gestão para Clínicas de Estética</h3>
            <p className="mt-2 text-slate-300">Para a rotina da clínica: quem chega, o que foi feito e como está o dia.</p>
            <ul className="mt-4 space-y-2 text-slate-100">
              <li>Agenda do dia</li>
              <li>Procedimentos e protocolos</li>
              <li>Estoque e financeiro da clínica</li>
            </ul>
            <Painel src="/homepage/clinica-tela.webp" alt="Painel da gestão para clínicas de estética" />
            <Link href="/solucoes/clinicas-estetica" className="mt-5 inline-flex rounded-full bg-[#2f6bff] px-5 py-2.5 text-sm font-semibold text-white">
              Conhecer o sistema
            </Link>
          </article>
        </div>
      </section>

      <section id="personalizados" className={`scroll-mt-24 border-t border-white/10 bg-[#04183f] ${FAIXA}`}>
        <h2 className="text-3xl font-bold tracking-tight">Desenvolvimento de sistemas personalizados</h2>
        <p className="mt-3 max-w-3xl text-lg text-slate-200">
          Quando a operação não cabe no CRM nem na clínica, a LWK desenvolve o software sob medida. Não há sistema pronto para outros segmentos.
        </p>
        <ul className="mt-8 grid gap-4 sm:grid-cols-3">
          {[
            ["A operação primeiro", "O levantamento parte da rotina real da empresa."],
            ["Feito para o processo", "Telas e regras do jeito que a equipe trabalha."],
            ["Depois da entrega", "Suporte para o sistema continuar em uso."],
          ].map(([titulo, texto]) => (
            <li key={titulo} className={CARTAO}>
              <p className="font-semibold">{titulo}</p>
              <p className="mt-2 text-sm leading-relaxed text-slate-300">{texto}</p>
            </li>
          ))}
        </ul>
        <Link href="/solucoes/personalizados" className="mt-8 inline-flex rounded-full bg-[#2f6bff] px-5 py-2.5 text-sm font-semibold text-white">
          Solicitar orçamento
        </Link>
      </section>

      <section id="beneficios" className={`scroll-mt-24 border-t border-white/10 ${FAIXA}`}>
        <h2 className="text-3xl font-bold tracking-tight">Benefícios e diferenciais</h2>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["Tecnologia e segurança", "Sistemas feitos para o uso diário, com cuidado sobre os dados."],
            ["Suporte especializado", "Quem atende conhece o produto que a empresa contratou."],
            ["Na nuvem", "A equipe acessa de onde estiver, no computador ou no celular."],
            ["Sob medida quando precisa", "O pronto cobre clínica e comercial. O resto vira projeto."],
          ].map(([titulo, texto]) => (
            <article key={titulo} className={CARTAO}>
              <h3 className="text-lg font-semibold">{titulo}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-300">{texto}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="planos" className={`scroll-mt-24 border-t border-white/10 bg-[#04183f] ${FAIXA}`}>
        <h2 className="text-3xl font-bold tracking-tight">Planos e proposta</h2>
        <p className="mt-3 max-w-3xl text-lg text-slate-200">
          Os valores publicados são os da gestão para clínicas. CRM e sistemas personalizados seguem sob consulta.
        </p>
        <div className="mt-8 grid gap-4 lg:grid-cols-3">
          <article className={CARTAO}>
            <h3 className="text-xl font-bold">Gestão para clínicas</h3>
            <p className="mt-2 text-slate-300">Planos com valores publicados, a partir de R$ 99,90 por mês.</p>
            <Link href="/planos" className="mt-5 inline-flex rounded-full bg-[#2f6bff] px-5 py-2.5 text-sm font-semibold text-white">Ver planos</Link>
          </article>
          <article className={CARTAO}>
            <h3 className="text-xl font-bold">CRM de Vendas</h3>
            <p className="mt-2 text-slate-300">Consulte nossas condições comerciais.</p>
            <Link href="/contato" className="mt-5 inline-flex rounded-full bg-[#2f6bff] px-5 py-2.5 text-sm font-semibold text-white">Solicitar proposta</Link>
          </article>
          <article className={CARTAO}>
            <h3 className="text-xl font-bold">Sistema personalizado</h3>
            <p className="mt-2 text-slate-300">O valor depende do que a operação precisa.</p>
            <Link href="/solucoes/personalizados" className="mt-5 inline-flex rounded-full bg-[#2f6bff] px-5 py-2.5 text-sm font-semibold text-white">Pedir orçamento</Link>
          </article>
        </div>
      </section>

      <section id="pedir-demonstracao" className={`scroll-mt-24 border-t border-white/10 bg-[#04183f] ${FAIXA}`}>
        <h2 className="text-3xl font-bold tracking-tight">Contato e demonstração</h2>
        <p className="mt-3 max-w-3xl text-lg text-slate-200">
          Escolha o CRM, a clínica ou um sistema personalizado. A mensagem do WhatsApp já leva o produto, o nome e a empresa.
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
