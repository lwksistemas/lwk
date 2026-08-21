"use client";

import { useCallback, useEffect, useState } from "react";
import { DollarSign, Eye, FileText, Mail, MessageCircle, Plus, Trash2, X } from "lucide-react";
import apiClient from "@/lib/api-client";
import { useToast } from "@/components/ui/Toast";
import { Modal } from "@/components/ui/Modal";
import { formatCurrency } from "@/lib/financeiro-helpers";
import type { ConsultaDetailTabPanelsProps } from "./tab-panels-types";

interface OrcamentoItem {
  id: number;
  procedure_id: number | null;
  nome_procedimento: string;
  valor_original: string;
  valor_customizado: string;
  quantidade: number;
  observacao_item: string;
  subtotal: string;
}

interface Orcamento {
  id: number;
  consulta_id: number;
  patient_name: string;
  professional_name: string;
  observacoes: string;
  valor_total: string;
  validade_dias: number;
  status: string;
  enviado_email: boolean;
  enviado_whatsapp: boolean;
  data_envio: string | null;
  created_at: string;
  itens: OrcamentoItem[];
}

interface Procedure {
  id: number;
  nome: string;
  preco: string;
  categoria: string;
}

const STATUS_LABEL: Record<string, string> = {
  RASCUNHO: "Rascunho",
  ENVIADO: "Enviado",
  ACEITO: "Aceito",
  RECUSADO: "Recusado",
};

function formatarObservacoesOrcamento(texto: string): string {
  const t = (texto || "").trim();
  if (!t) return "";
  if (t.includes("\n")) return t;
  return t
    .replace(/\s+(?=Dados do Cliente:)/gi, "\n")
    .replace(/\s+(?=Empresa:)/gi, "\n")
    .replace(/\s+(?=CPF\/CNPJ:)/gi, "\n")
    .replace(/\s+(?=E-mails?:)/gi, "\n")
    .replace(/\s+(?=Telefone:)/gi, "\n")
    .replace(/\s+(?=Endere[cç]o:)/gi, "\n")
    .replace(/\s+(?=LGPD)/g, "\n")
    .trim();
}

export function OrcamentoTabPanel({ selected }: ConsultaDetailTabPanelsProps) {
  const toast = useToast();
  const [orcamentos, setOrcamentos] = useState<Orcamento[]>([]);
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [loading, setLoading] = useState(true);
  const [criando, setCriando] = useState(false);
  const [showForm, setShowForm] = useState(false);

  // Form state
  const [selectedProc, setSelectedProc] = useState("");
  const [valorCustom, setValorCustom] = useState("");
  const [quantidade, setQuantidade] = useState("1");
  const [itensForm, setItensForm] = useState<{ procedure_id: number; nome: string; valor: string; qtd: number }[]>([]);
  const [observacoes, setObservacoes] = useState("");
  const [showProcSelector, setShowProcSelector] = useState(true);
  const [visualizando, setVisualizando] = useState<Orcamento | null>(null);
  const [abrindoPdf, setAbrindoPdf] = useState<number | null>(null);

  const carregarOrcamentos = useCallback(async () => {
    if (!selected?.id) return;
    try {
      const { data } = await apiClient.get(`/clinica-beleza/orcamentos/?consulta_id=${selected.id}`);
      setOrcamentos(Array.isArray(data) ? data : []);
    } catch {
      // silencioso
    } finally {
      setLoading(false);
    }
  }, [selected?.id]);

  const carregarProcedimentos = useCallback(async () => {
    try {
      const { data } = await apiClient.get("/clinica-beleza/procedures/?page_size=200&active=true");
      setProcedures(data.results || data || []);
    } catch {
      // silencioso
    }
  }, []);

  useEffect(() => {
    carregarOrcamentos();
    carregarProcedimentos();
  }, [carregarOrcamentos, carregarProcedimentos]);

  const adicionarItem = () => {
    if (!selectedProc) return;
    const proc = procedures.find((p) => p.id === Number(selectedProc));
    if (!proc) return;
    const valor = valorCustom || proc.preco;
    setItensForm((prev) => [
      ...prev,
      { procedure_id: proc.id, nome: proc.nome, valor, qtd: Number(quantidade) || 1 },
    ]);
    setSelectedProc("");
    setValorCustom("");
    setQuantidade("1");
  };

  const removerItem = (idx: number) => {
    setItensForm((prev) => prev.filter((_, i) => i !== idx));
  };

  const criarOrcamento = async () => {
    if (itensForm.length === 0) {
      toast.warning("Adicione ao menos um procedimento.");
      return;
    }
    setCriando(true);
    try {
      await apiClient.post("/clinica-beleza/orcamentos/", {
        consulta_id: selected.id,
        observacoes,
        itens: itensForm.map((it) => ({
          procedure_id: it.procedure_id,
          valor_customizado: it.valor,
          quantidade: it.qtd,
        })),
      });
      toast.success("Orçamento criado!");
      setShowForm(false);
      setItensForm([]);
      setObservacoes("");
      await carregarOrcamentos();
    } catch {
      toast.error("Erro ao criar orçamento.");
    } finally {
      setCriando(false);
    }
  };

  const visualizarPdf = async (id: number) => {
    setAbrindoPdf(id);
    try {
      const res = await apiClient.get(`/clinica-beleza/orcamentos/${id}/pdf/`, { responseType: "blob" });
      const blob = res.data instanceof Blob ? res.data : new Blob([res.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      window.open(url, "_blank");
      setTimeout(() => window.URL.revokeObjectURL(url), 10000);
    } catch {
      toast.error("Erro ao gerar PDF.");
    } finally {
      setAbrindoPdf(null);
    }
  };

  const enviar = async (id: number, canal: "email" | "whatsapp") => {
    try {
      const { data } = await apiClient.post(`/clinica-beleza/orcamentos/${id}/enviar/`, { canais: [canal] });
      const result = data[canal];
      if (result?.sucesso) {
        toast.success(`Orçamento enviado por ${canal === "email" ? "e-mail" : "WhatsApp"}!`);
        await carregarOrcamentos();
      } else {
        toast.error(result?.erro || `Falha ao enviar por ${canal}.`);
      }
    } catch {
      toast.error(`Erro ao enviar por ${canal}.`);
    }
  };

  const excluir = async (id: number) => {
    if (!confirm("Excluir este orçamento?")) return;
    try {
      await apiClient.delete(`/clinica-beleza/orcamentos/${id}/`);
      toast.success("Orçamento excluído.");
      await carregarOrcamentos();
    } catch {
      toast.error("Erro ao excluir.");
    }
  };

  const editarOrcamento = (orc: Orcamento) => {
    // Preencher formulário com dados do orçamento existente
    setItensForm(
      orc.itens.map((it) => ({
        procedure_id: it.procedure_id || 0,
        nome: it.nome_procedimento,
        valor: it.valor_customizado,
        qtd: it.quantidade,
      }))
    );
    setObservacoes(orc.observacoes);
    setShowForm(true);
    // Excluir o orçamento antigo ao criar o novo (substituição)
    excluir(orc.id);
  };

  const totalForm = itensForm.reduce((acc, it) => acc + Number(it.valor) * it.qtd, 0);

  if (loading) {
    return <div className="p-6 text-center text-gray-500">Carregando...</div>;
  }

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <DollarSign size={20} /> Orçamentos
        </h3>
        <button
          type="button"
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-white rounded-lg"
          style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
        >
          <Plus size={16} /> Novo Orçamento
        </button>
      </div>

      {/* Formulário */}
      {showForm && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-4">
          <h4 className="font-medium text-gray-900 dark:text-white">Novo Orçamento</h4>

          {/* Adicionar procedimento — ocultar após adicionar itens */}
          {itensForm.length === 0 || showProcSelector ? (
            <div className="flex flex-wrap gap-2 items-end">
              <div className="flex-1 min-w-[200px]">
                <label className="block text-xs text-gray-500 mb-1">Procedimento</label>
                <select
                  value={selectedProc}
                  onChange={(e) => {
                    setSelectedProc(e.target.value);
                    const p = procedures.find((pr) => pr.id === Number(e.target.value));
                    if (p) setValorCustom(p.preco);
                  }}
                  className="w-full px-3 py-2 text-sm border rounded-lg bg-white dark:bg-gray-900 dark:border-gray-600"
                >
                  <option value="">Selecione...</option>
                  {procedures.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nome} — R$ {Number(p.preco).toFixed(2)}
                    </option>
                  ))}
                </select>
              </div>
              <div className="w-28">
                <label className="block text-xs text-gray-500 mb-1">Valor (R$)</label>
                <input
                  type="number"
                  step="0.01"
                  value={valorCustom}
                  onChange={(e) => setValorCustom(e.target.value)}
                  className="w-full px-3 py-2 text-sm border rounded-lg bg-white dark:bg-gray-900 dark:border-gray-600"
                />
              </div>
              <div className="w-16">
                <label className="block text-xs text-gray-500 mb-1">Qtd</label>
                <input
                  type="number"
                  min="1"
                  value={quantidade}
                  onChange={(e) => setQuantidade(e.target.value)}
                  className="w-full px-3 py-2 text-sm border rounded-lg bg-white dark:bg-gray-900 dark:border-gray-600"
                />
              </div>
              <button
                type="button"
                onClick={() => { adicionarItem(); setShowProcSelector(false); }}
                disabled={!selectedProc}
                className="px-3 py-2 text-sm bg-green-600 text-white rounded-lg disabled:opacity-50"
              >
                Adicionar
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setShowProcSelector(true)}
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              + Adicionar mais procedimentos
            </button>
          )}

          {/* Lista de itens */}
          {itensForm.length > 0 && (
            <div className="border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-3 py-2 text-left">Procedimento</th>
                    <th className="px-3 py-2 text-right">Valor</th>
                    <th className="px-3 py-2 text-center">Qtd</th>
                    <th className="px-3 py-2 text-right">Subtotal</th>
                    <th className="px-3 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {itensForm.map((it, idx) => (
                    <tr key={idx} className="border-t">
                      <td className="px-3 py-2">{it.nome}</td>
                      <td className="px-3 py-2 text-right">{formatCurrency(it.valor)}</td>
                      <td className="px-3 py-2 text-center">{it.qtd}</td>
                      <td className="px-3 py-2 text-right font-medium">
                        {formatCurrency(Number(it.valor) * it.qtd)}
                      </td>
                      <td className="px-3 py-2 text-center">
                        <button type="button" onClick={() => removerItem(idx)} className="text-red-500 hover:text-red-700">
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t bg-gray-50 dark:bg-gray-700">
                    <td colSpan={3} className="px-3 py-2 font-bold text-right">TOTAL:</td>
                    <td className="px-3 py-2 text-right font-bold">{formatCurrency(totalForm)}</td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          )}

          {/* Observações */}
          <div>
            <label className="block text-xs text-gray-500 mb-1">Observações (opcional)</label>
            <textarea
              value={observacoes}
              onChange={(e) => setObservacoes(e.target.value)}
              rows={5}
              className="w-full px-3 py-2 text-sm border rounded-lg bg-white dark:bg-gray-900 dark:border-gray-600"
              placeholder="Condições de pagamento, validade especial... (aparecem no PDF; o WhatsApp envia só o resumo + anexo)"
            />
          </div>

          {/* Botões */}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => { setShowForm(false); setItensForm([]); }}
              className="px-4 py-2 text-sm border rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={criarOrcamento}
              disabled={criando || itensForm.length === 0}
              className="px-4 py-2 text-sm text-white rounded-lg disabled:opacity-50"
              style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
            >
              {criando ? "Criando..." : "Criar Orçamento"}
            </button>
          </div>
        </div>
      )}

      {/* Lista de orçamentos existentes */}
      {orcamentos.length === 0 && !showForm && (
        <div className="text-center py-8 text-gray-500">
          <DollarSign size={40} className="mx-auto mb-2 opacity-30" />
          <p>Nenhum orçamento criado para esta consulta.</p>
          <p className="text-xs mt-1">Clique em "Novo Orçamento" para criar.</p>
        </div>
      )}

      {orcamentos.map((orc) => (
        <div
          key={orc.id}
          className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-lg font-semibold text-gray-900 dark:text-white">
                {formatCurrency(orc.valor_total)}
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                {STATUS_LABEL[orc.status] || orc.status}
              </span>
              {orc.enviado_email && <span className="text-xs text-green-600">✓ E-mail</span>}
              {orc.enviado_whatsapp && <span className="text-xs text-green-600">✓ WhatsApp</span>}
            </div>
            <span className="text-xs text-gray-500">
              {new Date(orc.created_at).toLocaleDateString("pt-BR")}
            </span>
          </div>

          <div className="text-sm text-gray-800 dark:text-gray-200 mb-3 space-y-1">
            {orc.itens.map((it) => (
              <div key={it.id} className="flex justify-between gap-3">
                <span className="break-words">
                  {it.nome_procedimento}{" "}
                  <span className="text-gray-500">({it.quantidade}x)</span>
                </span>
                <span className="shrink-0 font-medium">{formatCurrency(it.subtotal)}</span>
              </div>
            ))}
          </div>

          {orc.observacoes && (
            <div className="mb-3 rounded-md bg-gray-50 dark:bg-gray-900/50 border border-gray-100 dark:border-gray-700 px-3 py-2 max-h-48 overflow-y-auto">
              <p className="text-xs font-medium text-gray-500 mb-1">Observações</p>
              <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap break-words leading-relaxed">
                {formatarObservacoesOrcamento(orc.observacoes)}
              </p>
            </div>
          )}

          <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-100 dark:border-gray-700">
            <button
              type="button"
              onClick={() => setVisualizando(orc)}
              className="flex items-center gap-1 px-3 py-1.5 text-xs bg-gray-100 text-gray-800 rounded hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600"
            >
              <Eye size={14} /> Visualizar
            </button>
            <button
              type="button"
              onClick={() => visualizarPdf(orc.id)}
              disabled={abrindoPdf === orc.id}
              className="flex items-center gap-1 px-3 py-1.5 text-xs bg-purple-50 text-purple-700 rounded hover:bg-purple-100 dark:bg-purple-900/20 dark:text-purple-300 disabled:opacity-50"
            >
              <FileText size={14} /> {abrindoPdf === orc.id ? "Abrindo..." : "PDF"}
            </button>
            <button
              type="button"
              onClick={() => enviar(orc.id, "email")}
              className="flex items-center gap-1 px-3 py-1.5 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100 dark:bg-blue-900/20 dark:text-blue-300"
            >
              <Mail size={14} /> Email
            </button>
            <button
              type="button"
              onClick={() => enviar(orc.id, "whatsapp")}
              className="flex items-center gap-1 px-3 py-1.5 text-xs bg-green-50 text-green-700 rounded hover:bg-green-100 dark:bg-green-900/20 dark:text-green-300"
            >
              <MessageCircle size={14} /> WhatsApp
            </button>
            <button
              type="button"
              onClick={() => editarOrcamento(orc)}
              className="flex items-center gap-1 px-3 py-1.5 text-xs bg-amber-50 text-amber-700 rounded hover:bg-amber-100 dark:bg-amber-900/20 dark:text-amber-300"
            >
              <Plus size={14} /> Editar
            </button>
            <button
              type="button"
              onClick={() => excluir(orc.id)}
              className="flex items-center gap-1 px-3 py-1.5 text-xs bg-red-50 text-red-700 rounded hover:bg-red-100 dark:bg-red-900/20 dark:text-red-300 ml-auto"
            >
              <Trash2 size={14} /> Excluir
            </button>
          </div>
        </div>
      ))}

      <Modal isOpen={!!visualizando} onClose={() => setVisualizando(null)} maxWidth="lg">
        {visualizando && (
          <div className="p-5">
            <div className="flex items-start justify-between gap-3 mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Orçamento</h3>
                <p className="text-sm text-gray-500 mt-0.5">
                  {visualizando.patient_name}
                  {visualizando.professional_name ? ` · ${visualizando.professional_name}` : ""}
                  {" · "}
                  {new Date(visualizando.created_at).toLocaleDateString("pt-BR")}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setVisualizando(null)}
                className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
                aria-label="Fechar"
              >
                <X size={18} />
              </button>
            </div>

            <table className="w-full text-sm mb-4">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-2 font-medium">Procedimento</th>
                  <th className="pb-2 font-medium text-center w-14">Qtd</th>
                  <th className="pb-2 font-medium text-right">Valor</th>
                </tr>
              </thead>
              <tbody>
                {visualizando.itens.map((it) => (
                  <tr key={it.id} className="border-b border-gray-100 dark:border-gray-700">
                    <td className="py-2 pr-2 text-gray-900 dark:text-gray-100 break-words">
                      {it.nome_procedimento}
                    </td>
                    <td className="py-2 text-center text-gray-600">{it.quantidade}</td>
                    <td className="py-2 text-right font-medium whitespace-nowrap">
                      {formatCurrency(it.subtotal)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <td colSpan={2} className="pt-3 text-right font-semibold">
                    Total
                  </td>
                  <td className="pt-3 text-right font-bold text-base">
                    {formatCurrency(visualizando.valor_total)}
                  </td>
                </tr>
              </tfoot>
            </table>

            {visualizando.observacoes && (
              <div className="mb-4">
                <p className="text-xs font-medium text-gray-500 mb-1">Observações</p>
                <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap break-words leading-relaxed">
                  {formatarObservacoesOrcamento(visualizando.observacoes)}
                </p>
              </div>
            )}

            <p className="text-xs text-gray-500 mb-4">
              Válido por {visualizando.validade_dias} dias · {STATUS_LABEL[visualizando.status] || visualizando.status}
            </p>

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => visualizarPdf(visualizando.id)}
                disabled={abrindoPdf === visualizando.id}
                className="flex items-center gap-1 px-4 py-2 text-sm text-white rounded-lg disabled:opacity-50"
                style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
              >
                <FileText size={16} /> {abrindoPdf === visualizando.id ? "Abrindo..." : "Abrir PDF"}
              </button>
              <button
                type="button"
                onClick={() => setVisualizando(null)}
                className="px-4 py-2 text-sm border rounded-lg"
              >
                Fechar
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
