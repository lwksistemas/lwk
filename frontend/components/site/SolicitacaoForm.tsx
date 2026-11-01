'use client';

import Link from "next/link";
import { useMemo, useState } from "react";
import { mensagemContato, mensagemDemonstracao, mensagemOrcamento, urlWhatsapp } from "@/lib/whatsapp-site";

const PRODUTOS = [
  { id: "crm-vendas", label: "CRM Vendas" },
  { id: "clinicas-estetica", label: "Gestão para Clínicas de Estética" },
  { id: "personalizados", label: "Sistemas personalizados" },
  { id: "outros", label: "Outro segmento" },
];

interface SolicitacaoFormProps {
  origem: "contato" | "demonstracao" | "orcamento";
  produtoInicial?: string;
  telefone?: string;
  mensagens?: Record<string, string>;
}

export function SolicitacaoForm({ origem, produtoInicial, telefone }: SolicitacaoFormProps) {
  const orcamento = origem === "orcamento";
  const demonstracao = origem === "demonstracao";
  const inicial = PRODUTOS.some((p) => p.id === produtoInicial) ? produtoInicial! : orcamento ? "personalizados" : "crm-vendas";
  const [produto, setProduto] = useState(orcamento ? "personalizados" : inicial);
  const [nome, setNome] = useState("");
  const [empresa, setEmpresa] = useState("");
  const [whatsapp, setWhatsapp] = useState("");
  const [segmento, setSegmento] = useState("");
  const [mensagem, setMensagem] = useState("");
  const [aceite, setAceite] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [ok, setOk] = useState(false);
  const [erro, setErro] = useState("");

  const textoWhatsapp = orcamento
    ? mensagemOrcamento(nome, empresa, segmento, mensagem)
    : demonstracao
      ? `${mensagemDemonstracao(produto, nome, empresa)}${mensagem.trim() ? ` ${mensagem.trim()}` : ""}`
      : mensagemContato(nome, empresa, mensagem);
  const url = useMemo(() => urlWhatsapp(telefone, textoWhatsapp), [telefone, textoWhatsapp]);

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault();
    setErro("");
    if ((demonstracao || orcamento) && !empresa.trim()) {
      setErro("Informe a empresa ou a clínica.");
      return;
    }
    if (orcamento && !segmento.trim()) {
      setErro("Informe o segmento de atuação.");
      return;
    }
    if (orcamento && !mensagem.trim()) {
      setErro("Descreva o sistema desejado.");
      return;
    }
    if (!orcamento && !demonstracao && !mensagem.trim()) {
      setErro("Escreva a mensagem.");
      return;
    }
    if (!aceite) {
      setErro("Marque o aviso de privacidade para enviar.");
      return;
    }
    const texto = orcamento
      ? mensagemOrcamento(nome, empresa, segmento, mensagem)
      : demonstracao
        ? `${mensagemDemonstracao(produto, nome, empresa)}${mensagem.trim() ? ` ${mensagem.trim()}` : ""}`
        : mensagem.trim();
    setEnviando(true);
    try {
      const base = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api").replace(/\/$/, "");
      const raiz = base.endsWith("/api") ? base : `${base}/api`;
      const resposta = await fetch(`${raiz}/site/contato/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          nome,
          empresa,
          whatsapp,
          produto: orcamento ? "personalizados" : produto,
          mensagem: texto,
          origem: orcamento ? "orcamento" : origem,
          aceite_lgpd: true,
        }),
      });
      if (!resposta.ok) {
        setErro("Não foi possível enviar. Confira os campos e tente de novo.");
        return;
      }
      setOk(true);
    } catch {
      setErro("Não foi possível enviar agora.");
    } finally {
      setEnviando(false);
    }
  }

  if (ok) {
    return (
      <p className="rounded-xl bg-green-50 p-4 text-green-800" role="status">
        Mensagem recebida. Vamos retornar no WhatsApp informado.
      </p>
    );
  }

  return (
    <form id="formulario" onSubmit={enviar} className="space-y-4">
      {!orcamento && (
        <fieldset>
          <legend className="mb-2 text-sm font-medium">Produto de interesse</legend>
          <div className="grid gap-2 sm:grid-cols-2">
            {PRODUTOS.filter((item) => demonstracao ? item.id === "crm-vendas" || item.id === "clinicas-estetica" || item.id === "personalizados" : true).map((item) => (
              <label key={item.id} className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                <input
                  type="radio"
                  name="produto"
                  value={item.id}
                  checked={produto === item.id}
                  onChange={() => setProduto(item.id)}
                  required
                />
                {item.label}
              </label>
            ))}
          </div>
        </fieldset>
      )}
      <label className="block text-sm">
        Nome
        <input required value={nome} onChange={(e) => setNome(e.target.value)} autoComplete="name" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
      </label>
      <label className="block text-sm">
        Empresa ou clínica
        <input required={demonstracao || orcamento} value={empresa} onChange={(e) => setEmpresa(e.target.value)} autoComplete="organization" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
      </label>
      <label className="block text-sm">
        WhatsApp
        <input required value={whatsapp} onChange={(e) => setWhatsapp(e.target.value)} inputMode="tel" autoComplete="tel" placeholder="16999998888" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
      </label>
      {orcamento && (
        <label className="block text-sm">
          Segmento de atuação
          <input required value={segmento} onChange={(e) => setSegmento(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
        </label>
      )}
      <label className="block text-sm">
        {orcamento ? "Descrição do sistema desejado" : "Mensagem"}
        <textarea required={!demonstracao} value={mensagem} onChange={(e) => setMensagem(e.target.value)} rows={4} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
      </label>
      {demonstracao && (
        <p className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-600">
          A mensagem do WhatsApp já inclui o produto, o nome e a empresa.
        </p>
      )}
      <label className="flex items-start gap-2 text-sm text-slate-600">
        <input type="checkbox" checked={aceite} onChange={(e) => setAceite(e.target.checked)} className="mt-1" />
        <span>
          Autorizo a LWK Sistemas a usar estes dados apenas para retornar este contato, conforme a LGPD.{" "}
          <Link href="/privacidade" className="font-medium text-blue-700 underline">Política de Privacidade</Link>.
        </span>
      </label>
      {erro && <p className="text-sm text-red-600" role="alert">{erro}</p>}
      <div className="flex flex-wrap gap-3">
        <button type="submit" disabled={enviando} className="rounded-full bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-60">
          {enviando ? "Enviando..." : orcamento ? "Solicitar orçamento" : demonstracao ? "Solicitar demonstração" : "Enviar"}
        </button>
        {url && (
          <a href={url} target="_blank" rel="noopener noreferrer" className="rounded-full bg-[#25D366] px-5 py-2.5 text-sm font-semibold text-white">
            Enviar pelo WhatsApp
          </a>
        )}
      </div>
    </form>
  );
}
