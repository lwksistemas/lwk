"use client";

import { useEffect, useState } from "react";
import { SalaoAPI, type ItemXmlSalao, type NotaPendenteSalao, type PreviewXmlSalao } from "@/lib/salao-api";

export function ImportarXmlModal({ aberto, onFechar, onImportou }: { aberto: boolean; onFechar: () => void; onImportou: () => void }) {
  const [pendentes, setPendentes] = useState<NotaPendenteSalao[]>([]);
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [preview, setPreview] = useState<PreviewXmlSalao | null>(null);
  const [itens, setItens] = useState<ItemXmlSalao[]>([]);
  const [erro, setErro] = useState("");
  const [aviso, setAviso] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const [resultado, setResultado] = useState("");

  useEffect(() => {
    if (!aberto) return;
    setErro("");
    setAviso("");
    setResultado("");
    setPreview(null);
    setArquivo(null);
    SalaoAPI.notasPendentes().then((dados) => setPendentes(dados.pendentes)).catch(() => setPendentes([]));
  }, [aberto]);

  if (!aberto) return null;

  function aplicarPreview(dados: PreviewXmlSalao) {
    setPreview(dados);
    setItens(dados.produtos);
    setAviso(dados.aviso_destinatario || "");
    setResultado("");
  }

  async function visualizar() {
    if (!arquivo || ocupado) return;
    setErro("");
    setOcupado(true);
    try {
      aplicarPreview(await SalaoAPI.enviarXml(arquivo));
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível ler o XML.");
    } finally {
      setOcupado(false);
    }
  }

  async function buscar() {
    if (ocupado) return;
    setErro("");
    setOcupado(true);
    try {
      const dados = await SalaoAPI.buscarNotasSefaz();
      setPendentes(dados.pendentes);
      setAviso(dados.detail);
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível consultar a SEFAZ.");
    } finally {
      setOcupado(false);
    }
  }

  async function abrir(id: number) {
    setErro("");
    setOcupado(true);
    try {
      aplicarPreview(await SalaoAPI.abrirNota(id));
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível abrir a nota.");
    } finally {
      setOcupado(false);
    }
  }

  async function confirmar() {
    if (!preview || ocupado) return;
    setErro("");
    setOcupado(true);
    try {
      const dados = await SalaoAPI.confirmarNota(preview.id, itens);
      setResultado(`${dados.criados} produto(s) novo(s), ${dados.atualizados} saldo(s) atualizado(s).`);
      setPreview(null);
      onImportou();
      const lista = await SalaoAPI.notasPendentes();
      setPendentes(lista.pendentes);
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível confirmar a nota.");
    } finally {
      setOcupado(false);
    }
  }

  async function ignorar(id: number) {
    setErro("");
    try {
      const dados = await SalaoAPI.ignorarNota(id);
      setPendentes(dados.pendentes);
    } catch (exc) {
      setErro(exc instanceof Error ? exc.message : "Não foi possível ignorar a nota.");
    }
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4" role="dialog" aria-modal="true">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-3xl bg-white p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold">Importar XML (NF-e)</h2>
            <p className="text-sm text-[#8a6e74]">O arquivo é manual. A busca na SEFAZ traz as notas do certificado do salão.</p>
          </div>
          <button type="button" onClick={onFechar} className="text-sm text-[#7a3044]">Fechar</button>
        </div>
        {erro ? <p className="mt-3 text-sm text-red-700">{erro}</p> : null}
        {aviso ? <p className="mt-3 text-sm text-[#8a6e74]">{aviso}</p> : null}
        {resultado ? <p className="mt-3 text-sm text-[#1f8a4c]">{resultado}</p> : null}

        {preview ? (
          <div className="mt-4 space-y-3">
            <p className="text-sm">NF {preview.nota.numero || "—"} · {preview.nota.fornecedor || "Fornecedor"} · {preview.nota.valor_total ? `R$ ${preview.nota.valor_total}` : ""}</p>
            {itens.map((item, indice) => (
              <div key={`${item.gtin}-${indice}`} className="grid grid-cols-[1fr_5rem_8rem] items-center gap-2 rounded-2xl border border-[#f0e4e7] p-3 text-sm">
                <span>
                  <span className="block font-medium">{item.nome}</span>
                  <span className="text-[#8a6e74]">{item.acao === "atualizar" ? "Já existe no estoque" : "Produto novo"}{item.gtin ? ` · ${item.gtin}` : ""}</span>
                </span>
                <input value={item.quantidade} onChange={(evento) => setItens(itens.map((atual, posicao) => posicao === indice ? { ...atual, quantidade: Number(evento.target.value) || 0 } : atual))} className="rounded-xl border border-[#eadfe2] px-2 py-1" />
                <button type="button" className="text-[#7a3044]" onClick={() => setItens(itens.map((atual, posicao) => posicao === indice ? { ...atual, acao: atual.acao === "ignorar" ? (atual.produto_id ? "atualizar" : "novo") : "ignorar" } : atual))}>
                  {item.acao === "ignorar" ? "Ignorado" : "Entrar"}
                </button>
              </div>
            ))}
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setPreview(null)} className="rounded-full border px-4 py-2 text-sm">Voltar</button>
              <button type="button" onClick={confirmar} disabled={ocupado} className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white disabled:opacity-60">{ocupado ? "Importando…" : "Confirmar importação"}</button>
            </div>
          </div>
        ) : (
          <div className="mt-4 space-y-4">
            <div className="rounded-2xl border border-[#f0e4e7] p-3">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium">Notas pendentes</p>
                <button type="button" onClick={buscar} disabled={ocupado} className="rounded-full border border-[#eadfe2] px-3 py-1 text-xs disabled:opacity-60">{ocupado ? "Consultando…" : "Buscar na SEFAZ"}</button>
              </div>
              {pendentes.length === 0 ? <p className="mt-2 text-xs text-[#8a6e74]">Nenhuma nota aguardando. A busca usa o certificado A1 do salão.</p> : (
                <ul className="mt-2 space-y-2">
                  {pendentes.map((nota) => (
                    <li key={nota.id} className="flex items-center justify-between gap-2 text-sm">
                      <span>NF {nota.numero || "—"} — {nota.fornecedor || "Fornecedor"}<span className="block text-xs text-[#8a6e74]">{nota.status_display}{nota.ultimo_erro ? ` · ${nota.ultimo_erro}` : ""}</span></span>
                      <span className="flex gap-2">
                        {nota.tem_xml ? <button type="button" className="text-[#7a3044]" onClick={() => abrir(nota.id)}>Abrir</button> : null}
                        <button type="button" className="text-[#8a6e74]" onClick={() => ignorar(nota.id)}>Ignorar</button>
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <label className="block text-sm">Arquivo XML da NF-e
              <input type="file" accept=".xml,text/xml" onChange={(evento) => { setArquivo(evento.target.files?.[0] || null); setErro(""); }} className="mt-1 block w-full text-sm" />
            </label>
            <div className="flex justify-end">
              <button type="button" onClick={visualizar} disabled={ocupado || !arquivo} className="rounded-full bg-[#7a3044] px-4 py-2 text-sm text-white disabled:opacity-60">{ocupado ? "Lendo…" : "Visualizar produtos"}</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
