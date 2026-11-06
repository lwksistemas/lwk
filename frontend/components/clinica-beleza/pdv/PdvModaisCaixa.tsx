import { Printer, X } from "lucide-react";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { quandoRecibo } from "./pdv-utils";
import { rosa, type FechamentoCaixa } from "./pdv-tipos";

export function PdvAbrirCaixa({
  aberto,
  onFechar,
  responsavelCaixa,
  onResponsavel,
  funcionarios,
  erro,
  salvando,
  onConfirmar,
}: {
  aberto: boolean;
  onFechar: () => void;
  responsavelCaixa: string;
  onResponsavel: (valor: string) => void;
  funcionarios: { id: number; nome: string }[];
  erro: string;
  salvando: boolean;
  onConfirmar: () => void;
}) {
  if (!aberto) return null;
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4" onClick={onFechar}>
      <div className="w-full max-w-md rounded-2xl bg-white p-5" onClick={(clique) => clique.stopPropagation()}>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Abrir caixa</h2>
          <button type="button" onClick={onFechar} aria-label="Fechar"><X size={16} /></button>
        </div>
        <p className="mb-3 text-sm text-gray-500">Caixa Recepção</p>
        <label className="mb-4 block text-sm text-gray-600">
          Operador do caixa
          <select value={responsavelCaixa} onChange={(e) => onResponsavel(e.target.value)} className="mt-1 w-full rounded-xl border px-3 py-2 text-sm">
            <option value="">Selecione o funcionário</option>
            {funcionarios.map((pessoa) => <option key={pessoa.id} value={pessoa.id}>{pessoa.nome}</option>)}
          </select>
        </label>
        {funcionarios.length === 0 && <p className="mb-3 text-sm text-gray-500">Nenhum funcionário ativo no cadastro.</p>}
        {erro && <p className="mb-3 text-sm text-red-600">{erro}</p>}
        <button type="button" disabled={salvando} onClick={onConfirmar} className="w-full rounded-xl py-3 text-sm font-semibold text-white disabled:opacity-50" style={{ backgroundColor: rosa }}>
          {salvando ? "Abrindo..." : "Abrir caixa"}
        </button>
      </div>
    </div>
  );
}

export function PdvPainelCaixa({
  painel,
  onFechar,
  resumoCaixa,
  onVoltarHistorico,
  onVerResumo,
  fechamentos,
  recebidoHoje,
  caixaAberto,
  caixaAReceber,
  vendasProdutos,
  caixaNome,
  caixaResponsavel,
  erro,
  onFecharCaixa,
  onImprimir,
}: {
  painel: "historico" | "fechamento" | null;
  onFechar: () => void;
  resumoCaixa: FechamentoCaixa | null;
  onVoltarHistorico: () => void;
  onVerResumo: (item: FechamentoCaixa) => void;
  fechamentos: FechamentoCaixa[];
  recebidoHoje: number;
  caixaAberto: boolean;
  caixaAReceber: number;
  vendasProdutos: number;
  caixaNome: string;
  caixaResponsavel: string;
  erro: string;
  onFecharCaixa: () => void;
  onImprimir: (resumo: FechamentoCaixa) => void;
}) {
  if (!painel) return null;
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4" onClick={onFechar}>
      <div className="max-h-[80vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-5" onClick={(clique) => clique.stopPropagation()}>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{resumoCaixa ? "Resumo do caixa" : painel === "historico" ? "Caixa fechado" : "Fechamento do caixa"}</h2>
          <button type="button" onClick={onFechar} aria-label="Fechar"><X size={16} /></button>
        </div>
        {painel === "historico" && resumoCaixa ? (
          <div className="space-y-3 text-sm">
            <button type="button" className="text-xs font-medium" style={{ color: rosa }} onClick={onVoltarHistorico}>Voltar ao histórico</button>
            <p className="flex justify-between gap-3"><span className="text-gray-500">Operador</span><strong className="text-right">{resumoCaixa.operador || "Operador"}</strong></p>
            <p className="flex justify-between gap-3"><span className="text-gray-500">Caixa</span><strong>{resumoCaixa.nome || "Recepção"}</strong></p>
            <p className="flex justify-between gap-3"><span className="text-gray-500">Aberto</span><strong className="text-right">{quandoRecibo(resumoCaixa.aberta_em)}</strong></p>
            <p className="flex justify-between gap-3"><span className="text-gray-500">Fechado</span><strong className="text-right">{quandoRecibo(resumoCaixa.fechada_em)}</strong></p>
            <p className="flex justify-between"><span>Recebido</span><strong>{formatCurrency(Number(resumoCaixa.recebido || 0))}</strong></p>
            <p className="flex justify-between"><span>Ainda a receber</span><strong>{formatCurrency(Number(resumoCaixa.a_receber || 0))}</strong></p>
            <p className="flex justify-between"><span>Vendas de produtos</span><strong>{formatCurrency(Number(resumoCaixa.vendas_produtos || 0))}</strong></p>
            <div className="space-y-2 border-t pt-2">
              {resumoCaixa.vendas.filter((item) => item.status !== "cancelada").length === 0 && <p className="text-gray-500">Nenhuma venda de produto nesta gaveta.</p>}
              {resumoCaixa.vendas.filter((item) => item.status !== "cancelada").map((item) => (
                <p key={item.id} className="flex justify-between gap-3"><span>{item.cliente}</span><strong>{formatCurrency(Number(item.total || 0))}</strong></p>
              ))}
            </div>
            <button type="button" onClick={() => onImprimir(resumoCaixa)} className="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-white" style={{ backgroundColor: rosa }}><Printer size={14} /> Imprimir</button>
          </div>
        ) : painel === "historico" ? (
          <div className="space-y-1 text-sm">
            {fechamentos.length === 0 && <p className="text-gray-500">Nenhum caixa fechado hoje.</p>}
            {fechamentos.map((item) => (
              <button key={item.id} type="button" onClick={() => onVerResumo(item)} className="flex w-full items-center justify-between gap-3 rounded-xl px-2 py-2 text-left hover:bg-gray-50">
                <span>
                  <span className="block font-medium" style={{ color: rosa }}>{item.operador || "Operador"}</span>
                  <span className="block text-xs text-gray-500">{item.nome || "Recepção"} • fechado {quandoRecibo(item.fechada_em)}</span>
                </span>
                <span className="text-xs text-gray-500">Ver resumo</span>
              </button>
            ))}
          </div>
        ) : (
          <div className="space-y-2 text-sm">
            <p className="flex justify-between"><span>Recebido hoje</span><strong>{formatCurrency(recebidoHoje)}</strong></p>
            <p className="flex justify-between"><span>Ainda a receber</span><strong>{formatCurrency(caixaAberto ? caixaAReceber : 0)}</strong></p>
            <p className="flex justify-between"><span>Vendas de produtos</span><strong>{formatCurrency(vendasProdutos)}</strong></p>
            <p className="pt-2 text-xs text-gray-500">{caixaAberto ? `Estes valores são do caixa ${caixaNome || "aberto"}${caixaResponsavel ? `, responsável ${caixaResponsavel}` : ""}. Ao fechar, o resumo zera para o próximo operador.` : "Caixa fechado. Recebido e vendas de produtos ficam zerados até a próxima abertura."} O lançamento continua no Financeiro.</p>
            {erro && <p className="pt-2 text-sm text-amber-800">{erro}</p>}
            {caixaAberto && <button type="button" onClick={onFecharCaixa} className="mt-3 rounded-xl px-4 py-2 text-white" style={{ backgroundColor: rosa }}>Fechar caixa</button>}
          </div>
        )}
      </div>
    </div>
  );
}
