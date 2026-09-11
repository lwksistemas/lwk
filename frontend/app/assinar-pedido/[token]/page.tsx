"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { Download, Eye, FileText } from "lucide-react";
import { getPrimaryApiBaseUrl } from "@/lib/api-base";

type ItemPedido = {
  id?: number;
  codigo: string;
  nome: string;
  quantidade: string;
  preco: string;
  subtotal: string;
};

type PedidoPublico = {
  numero: number;
  loja_nome?: string;
  nome_assinante?: string;
  ja_assinado?: boolean;
  error?: string;
  fornecedor?: { razao_social: string; cnpj: string };
  valor_total?: string;
  itens?: ItemPedido[];
};

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
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <h1 className="text-xl font-semibold mb-1">Assinar pedido de compra</h1>
        {data?.loja_nome && <p className="text-sm text-gray-500 mb-4">{data.loja_nome}</p>}
        {loading && <p className="text-sm text-gray-500">Carregando…</p>}
        {erro && <p className="text-sm text-red-600 mb-3">{erro}</p>}
        {ok && <p className="text-sm text-green-700 mb-3">Pedido assinado. Obrigado.</p>}
        {data && !loading && (
          <p className="text-sm mb-4">
            Pedido nº {data.numero}
            {data.fornecedor ? ` — ${data.fornecedor.razao_social}` : ""}
            {data.valor_total ? ` · Total R$ ${data.valor_total}` : ""}
          </p>
        )}

        {data && !loading && (
          <div className="mb-6">
            <div className="rounded-lg border border-dashed border-gray-300 bg-white px-4 py-6 text-center">
              <FileText className="mx-auto mb-2 h-10 w-10 text-gray-400" aria-hidden />
              <p className="text-sm font-medium">PDF do pedido</p>
              <p className="mt-1 text-xs text-gray-600">
                Abra em nova aba ou baixe o arquivo para conferir os itens antes de assinar.
              </p>
            </div>
            <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <a
                href={pdfHref}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 rounded-lg border bg-white px-4 py-3 text-sm font-medium hover:bg-gray-50"
              >
                <Eye className="h-4 w-4" />
                Visualizar PDF
              </a>
              <button
                type="button"
                disabled={baixando}
                onClick={() => void baixarPdf()}
                className="flex items-center justify-center gap-2 rounded-lg border bg-white px-4 py-3 text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
              >
                <Download className="h-4 w-4" />
                {baixando ? "Baixando…" : "Baixar PDF"}
              </button>
            </div>
          </div>
        )}

        {itens.length > 0 && (
          <div className="mb-6 overflow-x-auto border rounded-lg bg-white">
            <table className="w-full text-sm">
              <thead className="bg-gray-100">
                <tr>
                  <th className="text-left p-2">Código</th>
                  <th className="text-left p-2">Produto</th>
                  <th className="text-right p-2">Qtd</th>
                  <th className="text-right p-2">Preço</th>
                  <th className="text-right p-2">Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {itens.map((item, idx) => (
                  <tr key={item.id ?? `${item.codigo}-${item.nome}-${idx}`} className="border-t">
                    <td className="p-2">{item.codigo}</td>
                    <td className="p-2">{item.nome}</td>
                    <td className="p-2 text-right">{item.quantidade}</td>
                    <td className="p-2 text-right">{item.preco}</td>
                    <td className="p-2 text-right">{item.subtotal}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!ok && !loading && !erro && (
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              className="flex-1 px-3 py-2 border rounded-lg"
              placeholder="Seu nome (quem assina)"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
            />
            <button
              type="button"
              disabled={assinando || !nome.trim()}
              onClick={() => void assinar()}
              className="px-4 py-2 rounded-lg text-white disabled:opacity-50"
              style={{ background: "#8B3D52" }}
            >
              {assinando ? "Assinando…" : "Assinar pedido"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
