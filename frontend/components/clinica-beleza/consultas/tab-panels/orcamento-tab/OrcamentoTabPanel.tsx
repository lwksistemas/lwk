"use client";

import { useCallback, useEffect, useState } from "react";
import { DollarSign, Plus } from "lucide-react";
import apiClient from "@/lib/api-client";
import { useToast } from "@/components/ui/Toast";
import type { ConsultaDetailTabPanelsProps } from "../tab-panels-types";
import { OrcamentoCard } from "./OrcamentoCard";
import { OrcamentoForm } from "./OrcamentoForm";
import { OrcamentoViewerModal } from "./OrcamentoViewerModal";
import type { ItemForm, Orcamento, Procedure } from "./types";

export function OrcamentoTabPanel({ selected }: ConsultaDetailTabPanelsProps) {
  const toast = useToast();
  const [orcamentos, setOrcamentos] = useState<Orcamento[]>([]);
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [loading, setLoading] = useState(true);
  const [criando, setCriando] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const [selectedProc, setSelectedProc] = useState("");
  const [valorCustom, setValorCustom] = useState("");
  const [quantidade, setQuantidade] = useState("1");
  const [itensForm, setItensForm] = useState<ItemForm[]>([]);
  const [observacoes, setObservacoes] = useState("");
  const [showProcSelector, setShowProcSelector] = useState(true);
  const [visualizando, setVisualizando] = useState<Orcamento | null>(null);
  const [abrindoPdf, setAbrindoPdf] = useState<number | null>(null);
  const [decidindoStatus, setDecidindoStatus] = useState<number | null>(null);

  useEffect(() => {
    if (!visualizando) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setVisualizando(null);
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [visualizando]);

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

  const decidirStatus = async (id: number, status: "ACEITO" | "RECUSADO") => {
    setDecidindoStatus(id);
    try {
      await apiClient.patch(`/clinica-beleza/orcamentos/${id}/`, { status });
      toast.success(status === "ACEITO" ? "Orçamento aceito." : "Orçamento recusado.");
      setVisualizando((atual) => (atual && atual.id === id ? { ...atual, status } : atual));
      await carregarOrcamentos();
    } catch {
      toast.error("Não foi possível atualizar o status.");
    } finally {
      setDecidindoStatus(null);
    }
  };

  const editarOrcamento = (orc: Orcamento) => {
    setItensForm(
      orc.itens.map((it) => ({
        procedure_id: it.procedure_id || 0,
        nome: it.nome_procedimento,
        valor: it.valor_customizado,
        qtd: it.quantidade,
      })),
    );
    setObservacoes(orc.observacoes);
    setShowForm(true);
    excluir(orc.id);
  };

  if (loading) {
    return <div className="p-6 text-center text-gray-500">Carregando...</div>;
  }

  return (
    <div className="p-4 space-y-4">
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

      {showForm && (
        <OrcamentoForm
          procedures={procedures}
          itensForm={itensForm}
          observacoes={observacoes}
          selectedProc={selectedProc}
          valorCustom={valorCustom}
          quantidade={quantidade}
          showProcSelector={showProcSelector}
          criando={criando}
          onSelectedProc={setSelectedProc}
          onValorCustom={setValorCustom}
          onQuantidade={setQuantidade}
          onAdicionar={adicionarItem}
          onRemover={(idx) => setItensForm((prev) => prev.filter((_, i) => i !== idx))}
          onObservacoes={setObservacoes}
          onShowProcSelector={setShowProcSelector}
          onCancelar={() => {
            setShowForm(false);
            setItensForm([]);
          }}
          onCriar={criarOrcamento}
        />
      )}

      {orcamentos.length === 0 && !showForm && (
        <div className="text-center py-8 text-gray-500">
          <DollarSign size={40} className="mx-auto mb-2 opacity-30" />
          <p>Nenhum orçamento criado para esta consulta.</p>
          <p className="text-xs mt-1">Clique em "Novo Orçamento" para criar.</p>
        </div>
      )}

      {orcamentos.map((orc) => (
        <OrcamentoCard
          key={orc.id}
          orc={orc}
          abrindoPdf={abrindoPdf}
          decidindoStatus={decidindoStatus}
          onVisualizar={setVisualizando}
          onPdf={visualizarPdf}
          onEnviar={enviar}
          onAceitar={(id) => decidirStatus(id, "ACEITO")}
          onRecusar={(id) => decidirStatus(id, "RECUSADO")}
          onEditar={editarOrcamento}
          onExcluir={excluir}
        />
      ))}

      {visualizando && (
        <OrcamentoViewerModal
          visualizando={visualizando}
          abrindoPdf={abrindoPdf}
          decidindoStatus={decidindoStatus}
          onClose={() => setVisualizando(null)}
          onPdf={visualizarPdf}
          onAceitar={(id) => decidirStatus(id, "ACEITO")}
          onRecusar={(id) => decidirStatus(id, "RECUSADO")}
        />
      )}
    </div>
  );
}
