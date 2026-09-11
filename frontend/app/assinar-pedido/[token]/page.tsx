"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getPrimaryApiBaseUrl } from "@/lib/api-base";

type PedidoPublico = {
  numero: number;
  loja_nome?: string;
  nome_assinante?: string;
  ja_assinado?: boolean;
  error?: string;
  fornecedor?: { razao_social: string; cnpj: string };
  valor_total?: string;
  itens?: { codigo: string; nome: string; quantidade: string; preco: string; subtotal: string }[];
};

export default function AssinarPedidoPage() {
  const params = useParams();
  const token = decodeURIComponent(String(params.token || ""));
  const tokenSeg = encodeURIComponent(token);
  const api = `${getPrimaryApiBaseUrl()}/clinica-beleza/assinar-pedido/${tokenSeg}`;

  const [data, setData] = useState<PedidoPublico | null>(null);
  const [erro, setErro] = useState("");
  const [loading, setLoading] = useState(true);
  const [nome, setNome] = useState("");
  const [assinando, setAssinando] = useState(false);
  const [ok, setOk] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

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
        const pdfRes = await fetch(`${api}/pdf/`);
        if (pdfRes.ok && !cancelled) {
          const blob = await pdfRes.blob();
          setPdfUrl(URL.createObjectURL(blob));
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

  useEffect(() => {
    return () => {
      if (pdfUrl) URL.revokeObjectURL(pdfUrl);
    };
  }, [pdfUrl]);

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
          <p className="text-sm mb-3">
            Pedido nº {data.numero}
            {data.fornecedor ? ` — ${data.fornecedor.razao_social}` : ""}
            {data.valor_total ? ` · Total R$ ${data.valor_total}` : ""}
          </p>
        )}
        {pdfUrl && (
          <iframe title="Pedido" src={pdfUrl} className="w-full h-[70vh] border rounded-lg bg-white mb-4" />
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
