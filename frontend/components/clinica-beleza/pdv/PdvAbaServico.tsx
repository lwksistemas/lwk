import { Plus, ShoppingCart, UserRound, X } from "lucide-react";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import type { Consulta, ConsultaProcedimento } from "@/components/clinica-beleza/consultas/consultas-types";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { Bloco, LinhaCarrinho } from "./PdvPecas";
import { rosa, type ProdutoLinha, type ProdutoOpcao } from "./pdv-tipos";

export function PdvAbaServico({
  selecionado,
  onLimparCliente,
  procedimentos,
  alteraServico,
  consulta,
  onRemoverServico,
  produtosConsulta,
  consultaFinalizada,
  onRecarregarProdutos,
  incluindo,
  escolha,
  onEscolha,
  salvando,
  catalogo,
  procedimentosCat,
  onIncluirProduto,
  onIncluirServico,
  onIncluir,
  observacao,
  onObservacao,
}: {
  selecionado: AgendaEventData | null;
  onLimparCliente: () => void;
  procedimentos: ConsultaProcedimento[];
  alteraServico: boolean;
  consulta: Consulta | null;
  onRemoverServico: (consultaId: number, procedimentoId: number) => void;
  produtosConsulta: ProdutoLinha[];
  consultaFinalizada: boolean;
  onRecarregarProdutos: (consultaId: number) => void;
  incluindo: "produto" | "servico" | null;
  escolha: string;
  onEscolha: (valor: string) => void;
  salvando: boolean;
  catalogo: ProdutoOpcao[];
  procedimentosCat: { id: number; nome: string }[];
  onIncluirProduto: () => void;
  onIncluirServico: () => void;
  onIncluir: (tipo: "produto" | "servico") => void;
  observacao: string;
  onObservacao: (valor: string) => void;
}) {
  return (
    <div className="space-y-4">
      <div>
        <p className="mb-1 text-xs font-medium text-gray-500">Cliente</p>
        <div className="flex items-center gap-2 rounded-xl border px-3 py-2">
          <UserRound size={16} className="text-gray-400" />
          <span className="flex-1 text-sm">{selecionado?.extendedProps?.patient_name || "Selecione um agendamento"}</span>
          {selecionado && <button type="button" onClick={onLimparCliente} aria-label="Limpar cliente"><X size={14} /></button>}
        </div>
      </div>
      <Bloco titulo="Procedimentos / Serviços">
        {procedimentos.map((item) => {
          const procedimentoId = item.appointment_procedure_id || 0;
          return (
            <LinhaCarrinho key={`${procedimentoId || item.id}-${item.nome}`} tipo="Serviço" nome={item.nome} detalhe="" valor={Number(item.valor || 0)} onRemove={alteraServico && consulta?.id && procedimentoId ? () => onRemoverServico(consulta.id, procedimentoId) : undefined} />
          );
        })}
      </Bloco>
      {(!consultaFinalizada || produtosConsulta.length > 0) && (
        <Bloco titulo="Produtos (cosméticos)">
          {produtosConsulta.map((item) => (
            <LinhaCarrinho key={item.id} tipo="Produto" nome={item.produto_nome} detalhe={`${Number(item.quantidade)} × ${formatCurrency(Number(item.preco_unitario || 0))}`} valor={Math.max(0, Number(item.quantidade) * Number(item.preco_unitario || 0) - Number(item.desconto || 0))} onRemove={!consultaFinalizada && consulta?.id ? () => void ClinicaBelezaAPI.consultas.produtos.remove(consulta.id, item.id).then(() => onRecarregarProdutos(consulta.id)) : undefined} />
          ))}
        </Bloco>
      )}
      {incluindo && ((incluindo === "produto" && !consultaFinalizada) || (incluindo === "servico" && alteraServico)) && (
        <div className="flex gap-2">
          <select value={escolha} onChange={(e) => onEscolha(e.target.value)} className="flex-1 rounded-xl border px-3 py-2 text-sm">
            <option value="">{incluindo === "produto" ? "Produto" : "Serviço"}</option>
            {(incluindo === "produto" ? catalogo : procedimentosCat).map((item) => (
              <option key={item.id} value={item.id}>{item.nome}</option>
            ))}
          </select>
          <button type="button" disabled={salvando || !escolha} onClick={() => void (incluindo === "produto" ? onIncluirProduto() : onIncluirServico())} className="rounded-xl px-3 text-sm text-white" style={{ backgroundColor: rosa }}>Incluir</button>
        </div>
      )}
      <div className="flex flex-wrap gap-2">
        {!consultaFinalizada && <button type="button" onClick={() => onIncluir("produto")} className="inline-flex items-center gap-1 rounded-full border px-3 py-2 text-sm" style={{ color: rosa, borderColor: rosa }}><ShoppingCart size={14} /> + Adicionar produto</button>}
        {alteraServico && <button type="button" onClick={() => onIncluir("servico")} className="inline-flex items-center gap-1 rounded-full border px-3 py-2 text-sm" style={{ color: rosa, borderColor: rosa }}><Plus size={14} /> + Adicionar serviço</button>}
      </div>
      {selecionado && !alteraServico && (
        <p className="text-xs text-gray-500">
          {selecionado.extendedProps?.status === "COMPLETED"
            ? "Com a consulta finalizada não é possível incluir ou remover procedimentos."
            : "Procedimentos só podem ser incluídos ou removidos com a cliente presente ou em atendimento."}
        </p>
      )}
      <label className="block text-sm text-gray-600">
        Observações (opcional)
        <textarea value={observacao} onChange={(e) => onObservacao(e.target.value)} onBlur={() => { if (consulta?.id) void ClinicaBelezaAPI.consultas.update(consulta.id, { observacoes_gerais: observacao }); }} placeholder="Adicionar uma observação à cobrança..." className="mt-1 w-full rounded-xl border px-3 py-2 text-sm" rows={3} />
      </label>
    </div>
  );
}
