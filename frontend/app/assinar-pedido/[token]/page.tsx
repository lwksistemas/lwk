"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { CheckCircle, Download, Eye, FileText } from "lucide-react";
import { getPrimaryApiBaseUrl } from "@/lib/api-base";

type ItemPedido = {
  id?: number;
  codigo: string;
  nome: string;
  quantidade: string;
  preco: string;
  subtotal: string;
};

type LojaPedido = {
  nome?: string;
  cnpj?: string;
  logo?: string;
  endereco?: string;
  telefone?: string;
  email?: string;
};

type PedidoPublico = {
  numero: number;
  loja_nome?: string;
  loja?: LojaPedido;
  nome_assinante?: string;
  ja_assinado?: boolean;
  error?: string;
  fornecedor?: { razao_social: string; cnpj: string };
  valor_total?: string;
  valor_total_display?: string;
  itens?: ItemPedido[];
  assinaturas?: {
    clinica?: { nome?: string; conselho?: string; cpf?: string; assinado?: boolean };
  };
};

function brl(raw?: string): string {
  const n = Number(String(raw || "0").replace(",", "."));
  if (!Number.isFinite(n)) return "R$ 0,00";
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export default function AssinarPedidoPage() {
  const params = useParams();
  const token = decodeURIComponent(String(params.token || ""));
  const tokenSeg = encodeURIComponent(token);
  const api = `${getPrimaryApiBaseUrl()}/clinica-beleza/assinar-pedido/${tokenSeg}`;
  const pdfHref = `${api}/pdf/`;
  const pdfDownloadHref = `${api}/pdf/?download=1`;

  const [data, setData] = useState<PedidoPublico | null>(null);
  const [erro, setErro] = useState("");
  const [loading, setLoading] = useState(true);
  const [nome, setNome] = useState("");
  const [assinando, setAssinando] = useState(false);
  const [baixando, setBaixando] = useState(false);
  const [ok, setOk] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(api);
        const json = await res.json();
        if (!res.ok) {
          if (!cancelled) setErro(json.error || "Link inválido.");
          return;
        }
        if (!cancelled) {
          setData(json);
          setNome(json.nome_assinante || "");
          if (json.ja_assinado) setOk(true);
        }
      } catch {
        if (!cancelled) setErro("Erro ao carregar. Verifique sua conexão.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [api]);

  const itens = useMemo(() => data?.itens || [], [data]);
  const loja = data?.loja;
  const clinica = data?.assinaturas?.clinica;
  const totalLabel = data?.valor_total_display || brl(data?.valor_total);

  const baixarPdf = async () => {
    setBaixando(true);
    try {
      const res = await fetch(pdfHref);
      if (!res.ok) throw new Error("pdf");
      const blob = await res.blob();
      const url = URL.createObjectURL(new Blob([blob], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = `pedido_compra_${data?.numero ?? "pedido"}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      window.location.href = pdfDownloadHref;
    } finally {
      setBaixando(false);
    }
  };

  const assinar = async () => {
    setAssinando(true);
    setErro("");
    try {
      const res = await fetch(api, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome }),
      });
      const json = await res.json();
      if (!res.ok) {
        setErro(json.error || "Não foi possível assinar.");
        return;
      }
      setOk(true);
    } catch {
      setErro("Erro ao assinar. Tente novamente.");
    } finally {
      setAssinando(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#f8eef1] to-[#f3f4f6] text-gray-900">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div className="px-6 py-5 text-white" style={{ background: "#8B3D52" }}>
            <div className="flex items-center gap-4">
              {loja?.logo ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={loja.logo} alt="" className="h-12 w-auto max-w-[140px] object-contain bg-white rounded-md p-1" />
              ) : null}
              <div>
                <p className="text-xs uppercase tracking-wide text-white/80">Pedido de compra</p>
                <h1 className="text-xl font-semibold">{loja?.nome || data?.loja_nome || "Clínica"}</h1>
                {loja?.cnpj && <p className="text-xs text-white/80 mt-0.5">CNPJ {loja.cnpj}</p>}
              </div>
            </div>
            {(loja?.endereco || loja?.telefone || loja?.email) && (
              <p className="text-xs text-white/80 mt-3">
                {[loja.endereco, loja.telefone, loja.email].filter(Boolean).join(" · ")}
              </p>
            )}
          </div>

          <div className="px-6 py-6 space-y-5">
            {loading && <p className="text-sm text-gray-500">Carregando…</p>}
            {erro && <p className="text-sm text-red-600">{erro}</p>}
            {ok && (
              <div className="flex items-start gap-3 rounded-xl bg-green-50 border border-green-200 p-4">
                <CheckCircle className="h-5 w-5 text-green-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-green-800">Pedido assinado</p>
                  <p className="text-xs text-green-700 mt-0.5">Obrigado. A clínica receberá a confirmação.</p>
                </div>
              </div>
            )}

            {data && !loading && (
              <>
                <div className="flex flex-wrap justify-between gap-3">
                  <div>
                    <p className="text-xs text-gray-500">Pedido</p>
                    <p className="text-lg font-semibold">nº {data.numero}</p>
                    {data.fornecedor && (
                      <p className="text-sm text-gray-600 mt-1">
                        {data.fornecedor.razao_social}
                        {data.fornecedor.cnpj ? ` · CNPJ ${data.fornecedor.cnpj}` : ""}
                      </p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">Total</p>
                    <p className="text-xl font-bold" style={{ color: "#8B3D52" }}>{totalLabel}</p>
                  </div>
                </div>

                {clinica?.assinado && (
                  <div className="rounded-xl bg-[#f8eef1] px-4 py-3 text-sm">
                    <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: "#8B3D52" }}>
                      Profissional responsável
                    </p>
                    <p className="font-medium mt-1">{clinica.nome}</p>
                    <p className="text-xs text-gray-600">
                      {[clinica.conselho, clinica.cpf ? `CPF ${clinica.cpf}` : ""].filter(Boolean).join(" · ")}
                    </p>
                  </div>
                )}

                <div>
                  <p className="text-sm font-medium mb-2">Documento do pedido</p>
                  <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 px-4 py-5 text-center">
                    <FileText className="mx-auto mb-2 h-9 w-9 text-gray-400" aria-hidden />
                    <p className="text-sm text-gray-600">
                      Confira o PDF com a logo da clínica, os dados da profissional e os itens antes de assinar.
                    </p>
                  </div>
                  <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <a
                      href={pdfHref}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-center gap-2 rounded-xl border bg-white px-4 py-3 text-sm font-medium hover:bg-gray-50"
                    >
                      <Eye className="h-4 w-4" />
                      Visualizar PDF
                    </a>
                    <button
                      type="button"
                      disabled={baixando}
                      onClick={() => void baixarPdf()}
                      className="flex items-center justify-center gap-2 rounded-xl border bg-white px-4 py-3 text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
                    >
                      <Download className="h-4 w-4" />
                      {baixando ? "Baixando…" : "Baixar PDF"}
                    </button>
                  </div>
                </div>

                {itens.length > 0 && (
                  <div className="overflow-x-auto border rounded-xl">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="text-left p-3 font-medium">Código</th>
                          <th className="text-left p-3 font-medium">Produto</th>
                          <th className="text-right p-3 font-medium">Qtd</th>
                          <th className="text-right p-3 font-medium">Preço</th>
                          <th className="text-right p-3 font-medium">Subtotal</th>
                        </tr>
                      </thead>
                      <tbody>
                        {itens.map((item, idx) => (
                          <tr key={item.id ?? `${item.codigo}-${idx}`} className="border-t">
                            <td className="p-3 whitespace-nowrap">{item.codigo}</td>
                            <td className="p-3">{item.nome}</td>
                            <td className="p-3 text-right">{item.quantidade}</td>
                            <td className="p-3 text-right">{brl(item.preco)}</td>
                            <td className="p-3 text-right">{brl(item.subtotal)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {!ok && !erro && (
                  <div className="rounded-xl border p-4 space-y-3">
                    <p className="text-sm font-medium">Assinatura do fornecedor</p>
                    <p className="text-xs text-gray-500">Informe o nome de quem confirma o pedido.</p>
                    <div className="flex flex-col sm:flex-row gap-2">
                      <input
                        className="flex-1 px-3 py-2.5 border rounded-xl"
                        placeholder="Nome de quem assina"
                        value={nome}
                        onChange={(e) => setNome(e.target.value)}
                      />
                      <button
                        type="button"
                        disabled={assinando || !nome.trim()}
                        onClick={() => void assinar()}
                        className="px-5 py-2.5 rounded-xl text-white font-medium disabled:opacity-50"
                        style={{ background: "#8B3D52" }}
                      >
                        {assinando ? "Assinando…" : "Assinar pedido"}
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
