"use client";

import { Plus } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import type { ConsultaPrintMeta } from "@/lib/consulta-print";
import { ProdutoAdicionarForm } from "./produtos/ProdutoAdicionarForm";
import { ProdutosEstoqueAlert } from "./produtos/ProdutosEstoqueAlert";
import { ProdutosListaTable } from "./produtos/ProdutosListaTable";
import { useConsultaProdutos } from "./produtos/useConsultaProdutos";

export type { ConsultaProdutoItem } from "./produtos/produtos-types";

export function ConsultaProdutosTab({
  consultaId,
  somenteLeitura,
  printMeta,
  onItensChanged,
}: {
  consultaId: number;
  somenteLeitura: boolean;
  printMeta: ConsultaPrintMeta;
  onItensChanged?: () => void;
}) {
  const {
    itens,
    produtos,
    loading,
    saving,
    showAddForm,
    produtoId,
    quantidade,
    lote,
    validade,
    erro,
    erroEstoque,
    totaisConsulta,
    avisoFormulario,
    produtosComEstoqueInsuficiente,
    setShowAddForm,
    setQuantidade,
    setLote,
    setValidade,
    onProdutoChange,
    adicionar,
    remover,
  } = useConsultaProdutos(consultaId, onItensChanged);

  if (loading) {
    return <div className="text-center py-12 text-gray-500 text-sm">Carregando produtos...</div>;
  }

  return (
    <div className="space-y-5">
      <p className="text-sm text-gray-600 dark:text-gray-400">
        Registre os produtos utilizados no atendimento. Ao <strong>finalizar a consulta</strong>, a quantidade será
        baixada automaticamente do estoque.
      </p>

      <ProdutosEstoqueAlert mensagens={produtosComEstoqueInsuficiente} />

      {!somenteLeitura && (
        <div className="space-y-3">
          {!showAddForm ? (
            <button
              type="button"
              onClick={() => setShowAddForm(true)}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-white text-sm font-medium"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              <Plus size={16} />
              Adicionar produto
            </button>
          ) : (
            <ProdutoAdicionarForm
              produtos={produtos}
              produtoId={produtoId}
              quantidade={quantidade}
              lote={lote}
              validade={validade}
              erro={erro}
              erroEstoque={erroEstoque}
              avisoFormulario={avisoFormulario}
              saving={saving}
              onProdutoChange={onProdutoChange}
              onQuantidadeChange={setQuantidade}
              onLoteChange={setLote}
              onValidadeChange={setValidade}
              onClose={() => setShowAddForm(false)}
              onAdicionar={() => void adicionar()}
            />
          )}
        </div>
      )}

      <ProdutosListaTable
        itens={itens}
        produtos={produtos}
        totaisConsulta={totaisConsulta}
        somenteLeitura={somenteLeitura}
        saving={saving}
        printMeta={printMeta}
        onRemover={(item) => void remover(item)}
      />
    </div>
  );
}
