"use client";

import { useCallback, useEffect, useState } from "react";
import { DollarSign, FileText, Mail, MessageCircle, Plus, Trash2 } from "lucide-react";
import apiClient from "@/lib/api-client";
import { useToast } from "@/components/ui/Toast";
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
    try {
      const res = await apiClient.get(`/clinica-beleza/orcamentos/${id}/pdf/`, { responseType: 'blob' });
      const blob = res.data instanceof Blob ? res.data : new Blob([res.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      window.open(url, "_blank");
      setTimeout(() => window.URL.revokeObjectURL(url), 10000);
    } catch {
      toast.error("Erro ao gerar PDF.");
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
                      <td className="px-3 py-2 text-right">R$ {Number(it.valor).toFixed(2)}</td>
                      <td className="px-3 py-2 text-center">{it.qtd}</td>
                      <td className="px-3 py-2 text-right font-medium">
                        R$ {(Number(it.valor) * it.qtd).toFixed(2)}
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
                    <td className="px-3 py-2 text-right font-bold">R$ {totalForm.toFixed(2)}</td>
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
              placeholder="Condições de pagamento, validade especial, informações adicionais..."
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
          <div className="flex items-center justify-between mb-2">
            <div>
              <span className="font-semibold text-gray-900 dark:text-white">
                R$ {Number(orc.valor_total).toFixed(2)}
              </span>
              <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                {orc.status}
              </span>
              {orc.enviado_email && <span className="ml-1 text-xs text-green-600">✓ Email</span>}
              {orc.enviado_whatsapp && <span className="ml-1 text-xs text-green-600">✓ WhatsApp</span>}
            </div>
            <span className="text-xs text-gray-500">
              {new Date(orc.created_at).toLocaleDateString("pt-BR")}
            </span>
          </div>

          {/* Itens */}
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
            {orc.itens.map((it) => (
              <div key={it.id} className="flex justify-between">
                <span>{it.nome_procedimento} x{it.quantidade}</span>
                <span>R$ {Number(it.subtotal).toFixed(2)}</span>
              </div>
            ))}
          </div>

          {orc.observacoes && (
            <p className="text-xs text-gray-500 italic mb-2">{orc.observacoes}</p>
          )}

          {/* Ações */}
          <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-100 dark:border-gray-700">
            <button
              type="button"
              onClick={() => visualizarPdf(orc.id)}
              className="flex items-center gap-1 px-3 py-1.5 text-xs bg-purple-50 text-purple-700 rounded hover:bg-purple-100 dark:bg-purple-900/20 dark:text-purple-300"
            >
              <FileText size={14} /> PDF
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
    </div>
  );
}
