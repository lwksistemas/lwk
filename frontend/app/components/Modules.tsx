import Link from "next/link";
import { Check, X } from "lucide-react";

interface BeneficioPlano {
  label: string;
  detalhe: string;
  incluso: boolean;
}

interface PlanoValor {
  nome: string;
  slug: string;
  resumo: string;
  precoMensal: string;
  precoAnual: string;
  storage: string;
  beneficios: BeneficioPlano[];
  destaque?: boolean;
}

const PLANOS_CLINICA: PlanoValor[] = [
  {
    nome: "Básico",
    slug: "basico-clinica-beleza",
    resumo: "Agenda, cadastro de pacientes e prontuário. Sem fotos no servidor, WhatsApp, NFS-e nem Memed.",
    precoMensal: "R$ 99,90",
    precoAnual: "R$ 999",
    storage: "1 GB",
    beneficios: [
      { label: "Agenda, pacientes e prontuário", detalhe: "Consultas, fichas e evolução clínica no dia a dia.", incluso: true },
      { label: "Fotos de acompanhamento", detalhe: "Upload e QR para fotos antes e depois.", incluso: false },
      { label: "WhatsApp", detalhe: "Confirmações e mensagens da agenda.", incluso: false },
      { label: "NFS-e e relatórios avançados", detalhe: "Nota fiscal de serviço e painéis de gestão.", incluso: false },
      { label: "Memed (prescrição digital)", detalhe: "Prescrição eletrônica na consulta.", incluso: false },
      { label: "Simulação estética", detalhe: "A clínica configura a própria chave YouCam.", incluso: false },
    ],
  },
  {
    nome: "Intermediário",
    slug: "intermediario-clinica-beleza",
    resumo: "Tudo do Básico, mais fotos de acompanhamento no servidor de mídia.",
    precoMensal: "R$ 149,90",
    precoAnual: "R$ 1.499",
    storage: "10 GB",
    beneficios: [
      { label: "Agenda, pacientes e prontuário", detalhe: "Consultas, fichas e evolução clínica no dia a dia.", incluso: true },
      { label: "Fotos de acompanhamento", detalhe: "Upload e QR para fotos antes e depois.", incluso: true },
      { label: "WhatsApp", detalhe: "Confirmações e mensagens da agenda.", incluso: false },
      { label: "NFS-e e relatórios avançados", detalhe: "Nota fiscal de serviço e painéis de gestão.", incluso: false },
      { label: "Memed (prescrição digital)", detalhe: "Prescrição eletrônica na consulta.", incluso: false },
      { label: "Simulação estética", detalhe: "A clínica configura a própria chave YouCam.", incluso: false },
    ],
  },
  {
    nome: "Completo",
    slug: "profissional-clinica-beleza",
    resumo: "Fotos, WhatsApp, NFS-e, relatórios, Memed e simulação estética com a chave da própria clínica.",
    precoMensal: "R$ 199,90",
    precoAnual: "R$ 1.999",
    storage: "25 GB",
    destaque: true,
    beneficios: [
      { label: "Agenda, pacientes e prontuário", detalhe: "Consultas, fichas e evolução clínica no dia a dia.", incluso: true },
      { label: "Fotos de acompanhamento", detalhe: "Upload e QR para fotos antes e depois.", incluso: true },
      { label: "WhatsApp", detalhe: "Confirmações e mensagens da agenda.", incluso: true },
      { label: "NFS-e e relatórios avançados", detalhe: "Nota fiscal de serviço e painéis de gestão.", incluso: true },
      { label: "Memed (prescrição digital)", detalhe: "Prescrição eletrônica na consulta.", incluso: true },
      { label: "Simulação estética", detalhe: "A clínica configura a própria chave YouCam.", incluso: true },
    ],
  },
];

const CARTAO = "rounded-2xl border border-cyan-300/50 bg-[#071833]/80 p-5 text-white";

function Marca({ incluso }: { incluso: boolean }) {
  return incluso ? (
    <Check className="inline-block h-4 w-4 text-sky-300" aria-label="Incluído" />
  ) : (
    <X className="inline-block h-4 w-4 text-slate-500" aria-label="Não incluído" />
  );
}

export default function Modules() {
  const recursos = PLANOS_CLINICA[0].beneficios.map((beneficio) => beneficio.label);

  return (
    <section className="w-full border-t border-white/10 bg-[#04183f] px-4 py-12 text-white sm:px-6 lg:px-8">
      <h2 className="text-3xl font-bold tracking-tight">Gestão para Clínicas de Estética</h2>
      <p className="mt-3 max-w-3xl text-lg text-slate-200">
        Três planos. O Básico cobre a rotina da clínica, o Intermediário libera as fotos e o Completo soma WhatsApp, NFS-e, relatórios, Memed e a simulação estética.
      </p>

      <div className="mt-8 overflow-x-auto">
        <table className="w-full min-w-[640px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-white/15 text-left">
              <th className="py-3 pr-4 font-semibold">Recurso</th>
              {PLANOS_CLINICA.map((plano) => (
                <th key={plano.nome} className="px-2 py-3 text-center font-semibold">
                  {plano.nome}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {recursos.map((recurso, indice) => (
              <tr key={recurso} className="border-b border-white/10">
                <td className="py-2.5 pr-4 text-slate-200">{recurso}</td>
                {PLANOS_CLINICA.map((plano) => (
                  <td key={plano.nome} className="px-2 py-2.5 text-center">
                    <Marca incluso={plano.beneficios[indice].incluso} />
                  </td>
                ))}
              </tr>
            ))}
            <tr>
              <td className="py-2.5 pr-4 text-slate-200">Armazenamento</td>
              {PLANOS_CLINICA.map((plano) => (
                <td key={plano.nome} className="px-2 py-2.5 text-center font-medium">
                  {plano.storage}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      <div className="mt-8 grid gap-4 lg:grid-cols-3">
        {PLANOS_CLINICA.map((plano) => (
          <article key={plano.nome} className={CARTAO}>
            {plano.destaque && (
              <p className="text-xs font-semibold uppercase tracking-wide text-sky-300">Mais completo</p>
            )}
            <h3 className="mt-1 text-xl font-bold">{plano.nome}</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-300">{plano.resumo}</p>
            <p className="mt-4 text-3xl font-bold">{plano.precoMensal}</p>
            <p className="text-sm text-slate-300">por mês · ou {plano.precoAnual}/ano</p>
            <ul className="mt-4 space-y-2 text-sm">
              {plano.beneficios.map((beneficio) => (
                <li key={beneficio.label} className="flex items-start gap-2">
                  <Marca incluso={beneficio.incluso} />
                  <span className={beneficio.incluso ? "text-slate-100" : "text-slate-500"}>{beneficio.label}</span>
                </li>
              ))}
            </ul>
            <Link
              href={`/cadastro?tipo=clinica-beleza&plano=${plano.slug}`}
              className="mt-5 inline-flex rounded-full bg-[#2f6bff] px-5 py-2.5 text-sm font-semibold text-white"
            >
              Começar
            </Link>
          </article>
        ))}
      </div>

      <h2 className="mt-14 text-3xl font-bold tracking-tight">CRM Vendas</h2>
      <p className="mt-3 max-w-3xl text-lg text-slate-200">
        O CRM Vendas não usa a tabela da clínica. O valor segue sob consulta.
      </p>
      <article className={`${CARTAO} mt-6 max-w-xl`}>
        <h3 className="text-xl font-bold">CRM Vendas</h3>
        <p className="mt-2 text-slate-300">Leads, funil, propostas, contratos e relatórios do comercial.</p>
        <p className="mt-4 text-2xl font-bold">Sob consulta</p>
        <Link href="/contato" className="mt-5 inline-flex rounded-full bg-[#2f6bff] px-5 py-2.5 text-sm font-semibold text-white">
          Solicitar proposta
        </Link>
      </article>

      <h2 className="mt-14 text-3xl font-bold tracking-tight">Sistemas personalizados</h2>
      <p className="mt-3 max-w-3xl text-lg text-slate-200">
        Não há plano pronto para outros segmentos. O valor depende da operação.
      </p>
      <article className={`${CARTAO} mt-6 max-w-xl`}>
        <h3 className="text-xl font-bold">Projeto sob medida</h3>
        <p className="mt-2 text-slate-300">O levantamento parte da rotina da empresa.</p>
        <p className="mt-4 text-2xl font-bold">Sob consulta</p>
        <Link href="/solucoes/personalizados" className="mt-5 inline-flex rounded-full bg-[#2f6bff] px-5 py-2.5 text-sm font-semibold text-white">
          Pedir orçamento
        </Link>
      </article>
    </section>
  );
}
