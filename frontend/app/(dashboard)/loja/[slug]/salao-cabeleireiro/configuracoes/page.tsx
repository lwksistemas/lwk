"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ChevronRight } from "lucide-react";
import { PainelDoSalao } from "@/components/salao/PaineisSalao";
import { SalaoAPI, type ComunicacaoSalao, type PainelSalao } from "@/lib/salao-api";

const OPCOES: { id: PainelSalao; nome: string; texto: string }[] = [
  { id: "operacao", nome: "Operação do dia", texto: "Cards do dia, gráfico da semana e a agenda de hoje." },
  { id: "semana", nome: "Agenda da semana", texto: "Grade de horários, clientes do dia e ocupação do salão." },
  { id: "gestao", nome: "Gestão do mês", texto: "Receita do mês, serviços mais vendidos e aniversariantes." },
];

const LISTA = [
  { titulo: "Layout do dashboard", descricao: "Operação do dia, agenda da semana ou gestão do mês.", href: "#layout", itens: ["Visualizar com dados de demonstração", "Gravar o layout do salão"] },
  { titulo: "Pagar assinatura", descricao: "Baixar boleto e ver o histórico de pagamentos.", href: "assinatura", itens: ["Baixar boleto", "Histórico de pagamento"] },
  { titulo: "Identidade visual", descricao: "Cor do menu, fundo das páginas e cores dos status da agenda.", href: "aparencia", itens: ["Cor do menu", "Fundo das páginas", "Cores dos status na agenda"] },
  { titulo: "Configurar tela de login", descricao: "Logo, fundo e cores da tela de login do salão.", href: "login", itens: ["Logo", "Imagem de fundo", "Cores do login"] },
  { titulo: "Contato no recibo", descricao: "Telefone, e-mail, endereço, documento, cor e logomarca do recibo.", href: "contato", itens: ["Telefone do salão", "Endereço e CPF ou CNPJ", "Cor e logomarca do recibo"] },
  { titulo: "Mensagens no WhatsApp", descricao: "Confirmação, lembrete, mudança de horário e cancelamento.", href: "#mensagens", itens: ["Confirmação de horário", "Lembrete", "Aviso de mudança e cancelamento"] },
  { titulo: "Funcionamento do salão", descricao: "Tipo de estabelecimento, recebimentos e permissões.", href: "funcionamento", itens: ["Salão com recepção", "Profissional autônomo", "Onde o pagamento é recebido"] },
  { titulo: "Nota fiscal (NFS-e)", descricao: "Provedor e certificado da nota de serviço.", href: "nota-fiscal", itens: ["Provedor de NF", "Certificado digital", "Emissão do serviço"] },
  { titulo: "Cupom fiscal (NFC-e)", descricao: "Cupom das vendas de produto. O recibo continua.", href: "cupom-fiscal", itens: ["Regime e CSC", "Inscrição estadual", "Homologação ou produção"] },
  { titulo: "Backup", descricao: "Exportar uma cópia dos dados deste salão.", href: "backup", itens: ["Exportar backup", "Clientes, agenda e caixa"] },
];

export default function ConfiguracoesSalaoPage() {
  const params = useParams();
  const slug = params.slug as string;
  const base = `/loja/${slug}/salao-cabeleireiro/configuracoes`;
  const [painel, setPainel] = useState<PainelSalao>("operacao");
  const [podeTrocar, setPodeTrocar] = useState(false);
  const [previa, setPrevia] = useState<PainelSalao | null>(null);
  const [confirmar, setConfirmar] = useState<PainelSalao | null>(null);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [layoutAberto, setLayoutAberto] = useState(false);
  const [mensagensAberto, setMensagensAberto] = useState(false);
  const layoutRef = useRef<HTMLDivElement>(null);
  const mensagensRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    SalaoAPI.config()
      .then((dados) => {
        setPainel(dados.painel);
        setPodeTrocar(dados.pode_trocar);
      })
      .catch((exc: Error) => setErro(exc.message));
  }, []);

  useEffect(() => {
    if (layoutAberto) layoutRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [layoutAberto]);

  useEffect(() => {
    if (mensagensAberto) mensagensRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [mensagensAberto]);

  async function escolher(proximo: PainelSalao) {
    if (!podeTrocar || proximo === painel) return;
    setErro("");
    setAviso("");
    try {
      await SalaoAPI.salvarPainel(proximo);
      setPainel(proximo);
      setConfirmar(null);
      setPrevia(null);
      window.dispatchEvent(new CustomEvent("salao-painel", { detail: proximo }));
      setAviso("Este layout ficou gravado no salão.");
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível gravar.");
    }
  }

  const nomeConfirmar = OPCOES.find((opcao) => opcao.id === confirmar)?.nome;
  const nomePrevia = OPCOES.find((opcao) => opcao.id === previa)?.nome;

  return (
    <div>
      <h1 className="mb-1 text-2xl font-semibold sm:text-3xl">Configurações</h1>
      <p className="mb-4 max-w-2xl text-sm text-[#8a6e74]">Assinatura, login, aparência, recibo, nota, cupom e backup deste salão.</p>
      <ul className="mb-8 grid gap-3 md:grid-cols-2">
        {LISTA.map((item) => {
          const painelLocal = item.href === "#layout" ? layoutAberto : item.href === "#mensagens" ? mensagensAberto : false;
          const conteudo = (
            <>
              <span className="min-w-0 text-left">
                <span className="block font-medium">{item.titulo}</span>
                <span className="mt-0.5 block text-sm text-[#8a6e74]">{item.descricao}</span>
                <span className="mt-1 block text-xs text-[#8a6e74]">{item.itens.join(" · ")}</span>
              </span>
              <ChevronRight size={18} className={`mt-1 shrink-0 text-[#8a6e74] ${painelLocal ? "rotate-90" : ""}`} />
            </>
          );
          if (item.href === "#layout" || item.href === "#mensagens") {
            const aberto = item.href === "#layout" ? layoutAberto : mensagensAberto;
            const alternar = item.href === "#layout"
              ? () => setLayoutAberto((valor) => !valor)
              : () => setMensagensAberto((valor) => !valor);
            return (
              <li key={item.titulo} className="overflow-hidden rounded-3xl border border-[#f0e4e6] bg-white">
                <button type="button" className="flex h-full w-full items-start justify-between gap-3 px-4 py-3 hover:bg-[#fbf6f4]" aria-expanded={aberto} onClick={alternar}>
                  {conteudo}
                </button>
              </li>
            );
          }
          const href = item.href === "assinatura" ? `/loja/${slug}/assinatura` : `${base}/${item.href}`;
          return (
            <li key={item.titulo} className="overflow-hidden rounded-3xl border border-[#f0e4e6] bg-white">
              <Link href={href} className="flex h-full items-start justify-between gap-3 px-4 py-3 hover:bg-[#fbf6f4]">
                {conteudo}
              </Link>
            </li>
          );
        })}
      </ul>
      {layoutAberto ? (
      <div id="layout" ref={layoutRef}>
      <h2 className="mb-1 text-xl font-semibold">Layout do dashboard</h2>
      <p className="mb-5 max-w-2xl text-sm text-[#8a6e74]">
        {podeTrocar
          ? "A prévia mostra clientes, horários, serviços e recebimentos de demonstração. Nada disso entra no salão. A troca pede confirmação e só o administrador grava."
          : "O layout em uso foi escolhido pelo administrador e fica fixo neste salão. A visualização usa cadastros de demonstração e não troca o modelo."}
      </p>
      {erro ? <p className="mb-3 text-sm text-red-700">{erro}</p> : null}
      {aviso ? <p className="mb-3 text-sm text-[#1f8a4c]">{aviso}</p> : null}
      {previa ? (
        <section className="mb-5 rounded-3xl border border-[#f0e4e6] bg-white p-4">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-[#8a6e74]">
              Prévia de {nomePrevia}. Os clientes, horários e valores são de demonstração e não ficam gravados.
              {previa === painel ? " Este é o layout em uso." : " Ainda não substitui o modelo em uso."}
            </p>
            <div className="flex flex-wrap gap-2">
              {podeTrocar && previa !== painel ? (
                <button type="button" className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" onClick={() => setConfirmar(previa)}>
                  Usar este layout
                </button>
              ) : null}
              <button type="button" className="rounded-full border px-4 py-2 text-sm" onClick={() => setPrevia(null)}>Fechar prévia</button>
            </div>
          </div>
          <PainelDoSalao painel={previa} demonstracao />
        </section>
      ) : null}
      <div className="grid gap-4 xl:grid-cols-3">
        {OPCOES.map((opcao) => {
          const ativo = painel === opcao.id;
          return (
            <article
              key={opcao.id}
              className={`rounded-3xl border bg-white p-3 text-left shadow-sm ${ativo ? "border-[#7a3044] ring-2 ring-[#7a3044]/40" : "border-[#f0e4e6]"}`}
            >
              <Miniatura id={opcao.id} />
              <span className="mt-3 flex items-center justify-between gap-2">
                <span className="font-medium">{opcao.nome}</span>
                {ativo ? <span className="rounded-full bg-[#7a3044] px-2 py-0.5 text-xs text-white">Em uso</span> : null}
              </span>
              <span className="mt-1 block text-sm text-[#8a6e74]">{opcao.texto}</span>
              <span className="mt-3 flex flex-wrap gap-2">
                <button type="button" className="rounded-full border px-3 py-1.5 text-sm" onClick={() => setPrevia(opcao.id)}>
                  Visualizar dashboard
                </button>
                {podeTrocar && !ativo ? (
                  <button type="button" className="rounded-full bg-[#7a3044] px-3 py-1.5 text-sm text-white" onClick={() => setConfirmar(opcao.id)}>
                    Usar este layout
                  </button>
                ) : null}
              </span>
            </article>
          );
        })}
      </div>
      </div>
      ) : null}
      {mensagensAberto ? (
        <div id="mensagens" ref={mensagensRef}>
          <MensagensWhatsapp />
        </div>
      ) : null}
      {confirmar ? (
        <div className="fixed inset-0 z-30 grid place-items-center bg-black/40 p-4" role="dialog" aria-modal="true" aria-labelledby="confirmar-layout">
          <div className="w-full max-w-md rounded-3xl bg-white p-5">
            <h2 id="confirmar-layout" className="text-lg font-semibold">Trocar o dashboard deste salão?</h2>
            <p className="mt-2 text-sm text-[#8a6e74]">A equipe passa a ver {nomeConfirmar}. A escolha fica gravada nesta loja.</p>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" className="rounded-full border px-4 py-2 text-sm" onClick={() => setConfirmar(null)}>Cancelar</button>
              <button type="button" className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" onClick={() => escolher(confirmar)}>Confirmar</button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function MensagensWhatsapp() {
  const params = useParams();
  const slug = params.slug as string;
  const [regras, setRegras] = useState<ComunicacaoSalao | null>(null);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");

  useEffect(() => {
    SalaoAPI.comunicacao().then(setRegras).catch((exc: Error) => setErro(exc.message));
  }, []);

  async function gravar() {
    if (!regras?.pode_gravar) return;
    setErro("");
    setAviso("");
    try {
      const salvo = await SalaoAPI.salvarComunicacao({
        confirmacao: regras.confirmacao,
        lembrete: regras.lembrete,
        lembrete_horas: regras.lembrete_horas,
        reagendamento: regras.reagendamento,
        cancelamento: regras.cancelamento,
      });
      setRegras(salvo);
      setAviso("As mensagens ficaram gravadas. Nada sai enquanto a opção estiver desligada.");
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível gravar.");
    }
  }

  if (!regras) return erro ? <p className="mt-6 text-sm text-red-700">{erro}</p> : null;
  const campo = (chave: "confirmacao" | "lembrete" | "reagendamento" | "cancelamento", nome: string) => (
    <label key={chave} className="flex items-center gap-2 text-sm">
      <input type="checkbox" checked={regras[chave]} disabled={!regras.pode_gravar} onChange={(evento) => setRegras({ ...regras, [chave]: evento.target.checked })} />
      {nome}
    </label>
  );

  return (
    <section className="mt-6 rounded-3xl border border-[#f0e4e6] bg-white p-4">
      <h2 className="text-lg font-semibold">Mensagens no WhatsApp</h2>
      <p className="mt-1 max-w-2xl text-sm text-[#8a6e74]">
        Confirmação, lembrete, mudança de horário e cancelamento. Tudo começa desligado. O número conectado é o da loja.
      </p>
      {regras.whatsapp_pronto ? null : <p className="mt-2 text-sm text-[#8a6e74]">O WhatsApp desta loja ainda não está conectado.</p>}
      <Link href={`/loja/${slug}/configuracoes/whatsapp`} className="mt-2 inline-block text-sm underline">Conectar WhatsApp</Link>
      <div className="mt-4 grid gap-2">
        {campo("confirmacao", "Confirmação de horário")}
        {campo("lembrete", "Lembrete antes do atendimento")}
        {campo("reagendamento", "Aviso quando o horário muda")}
        {campo("cancelamento", "Aviso de cancelamento")}
        <label className="flex items-center gap-2 text-sm">
          Lembrete
          <select className="rounded-lg border px-2 py-1" value={regras.lembrete_horas} disabled={!regras.pode_gravar || !regras.lembrete} onChange={(evento) => setRegras({ ...regras, lembrete_horas: Number(evento.target.value) })}>
            <option value={24}>24 horas antes</option>
            <option value={2}>2 horas antes</option>
          </select>
        </label>
      </div>
      {erro ? <p className="mt-3 text-sm text-red-700">{erro}</p> : null}
      {aviso ? <p className="mt-3 text-sm text-[#1f8a4c]">{aviso}</p> : null}
      {regras.pode_gravar ? <button type="button" className="mt-4 rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white" onClick={gravar}>Gravar mensagens</button> : null}
    </section>
  );
}

function Miniatura({ id }: { id: PainelSalao }) {
  if (id === "semana") return <MiniaturaSemana />;
  if (id === "gestao") return <MiniaturaGestao />;
  return <MiniaturaOperacao />;
}

function MiniaturaOperacao() {
  return (
    <div className="flex h-40 overflow-hidden rounded-2xl bg-[#fbf6f4]">
      <div className="w-9 bg-[#7A3044]" />
      <div className="flex min-w-0 flex-1 flex-col gap-1.5 p-2">
        <div className="h-2 w-16 rounded bg-[#7A3044]/25" />
        <div className="grid grid-cols-4 gap-1">
          {["#f3d5dc", "#f7e4c8", "#f8d7de", "#f3e6cf"].map((cor) => (
            <div key={cor} className="h-7 rounded-md bg-white p-1">
              <i className="block h-1.5 w-3 rounded" style={{ background: cor }} />
            </div>
          ))}
        </div>
        <div className="grid min-h-0 flex-1 grid-cols-[1.3fr_.8fr] gap-1">
          <div className="flex items-end gap-1 rounded-md bg-white px-1 pb-1">
            {[28, 40, 36, 48, 62, 52, 8].map((altura) => (
              <i key={altura} className="flex-1 rounded-t bg-[#d7a3ae]" style={{ height: altura }} />
            ))}
          </div>
          <div className="flex flex-col justify-center gap-1 rounded-md bg-white px-1">
            {[0, 1, 2].map((item) => <i key={item} className="h-1.5 rounded bg-[#f3d5dc]" />)}
          </div>
        </div>
      </div>
    </div>
  );
}

function MiniaturaSemana() {
  return (
    <div className="flex h-40 overflow-hidden rounded-2xl bg-[#f6f4fb]">
      <div className="w-9 bg-[#4c1d78]" />
      <div className="flex min-w-0 flex-1 gap-1 p-2">
        <div className="grid flex-1 grid-cols-5 gap-0.5 rounded-md bg-white p-1">
          {Array.from({ length: 15 }, (_, indice) => (
            <i key={indice} className={`rounded-sm ${indice % 4 === 0 ? "bg-[#ddd6fe]" : "bg-[#f5f3ff]"}`} />
          ))}
        </div>
        <div className="flex w-12 flex-col gap-1">
          <i className="h-8 rounded-md bg-white" />
          <i className="h-8 rounded-full bg-[#c4b5fd]" />
        </div>
      </div>
    </div>
  );
}

function MiniaturaGestao() {
  return (
    <div className="flex h-40 overflow-hidden rounded-2xl bg-[#f7f4ee]">
      <div className="w-9 bg-[#3d5244]" />
      <div className="flex min-w-0 flex-1 flex-col gap-1.5 p-2">
        <div className="h-2 w-20 rounded bg-[#3d5244]/25" />
        <div className="grid grid-cols-4 gap-1">
          {Array.from({ length: 4 }, (_, indice) => <i key={indice} className="h-6 rounded-md bg-[#e7f0df]" />)}
        </div>
        <div className="grid min-h-0 flex-1 grid-cols-2 gap-1">
          <div className="flex items-end gap-0.5 rounded-md bg-white px-1 pb-1">
            {[18, 24, 20, 30, 28, 36, 32].map((altura) => (
              <i key={altura} className="flex-1 rounded-t bg-[#8aaa78]" style={{ height: altura }} />
            ))}
          </div>
          <div className="rounded-md bg-white" />
        </div>
      </div>
    </div>
  );
}
