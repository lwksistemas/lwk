import type { Dispatch, SetStateAction } from "react";
import type { Consulta, ConsultaProcedimento } from "@/components/clinica-beleza/consultas/consultas-types";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import { PdvAbaServico } from "./PdvAbaServico";
import { PdvAbaVenda } from "./PdvAbaVenda";
import { rosa, type ProdutoLinha, type ProdutoOpcao, type VendaLinha } from "./pdv-tipos";

export function PdvColunaMeio({
  aba,
  onAba,
  erro,
  servico,
  venda,
}: {
  aba: "servico" | "venda";
  onAba: (aba: "servico" | "venda") => void;
  erro: string;
  servico: {
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
  };
  venda: {
    onAlternarNovoCliente: () => void;
    buscaCliente: string;
    onBuscaCliente: (valor: string) => void;
    pacienteVenda: number | "";
    clientes: { id: number; nome: string; telefone?: string; email?: string }[];
    onEscolherCliente: (cliente: { id: number; nome: string; telefone?: string; email?: string }) => void;
    telefoneRecibo: string;
    onTelefoneRecibo: (valor: string) => void;
    emailRecibo: string;
    onEmailRecibo: (valor: string) => void;
    novoCliente: boolean;
    nomeNovo: string;
    onNomeNovo: (valor: string) => void;
    telefoneNovo: string;
    onTelefoneNovo: (valor: string) => void;
    cpfNovo: string;
    onCpfNovo: (valor: string) => void;
    onClienteCriado: (id: number, nome: string, telefone: string) => void;
    buscaProduto: string;
    onBuscaProduto: (valor: string) => void;
    onEnterProduto: () => void;
    sugestoes: ProdutoOpcao[];
    onAdicionarProduto: (produto: ProdutoOpcao) => void;
    produtosConsultados: boolean;
    linhasVenda: VendaLinha[];
    setLinhasVenda: Dispatch<SetStateAction<VendaLinha[]>>;
  };
}) {
  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-4">
      <div className="mb-4 flex gap-2">
        <button type="button" onClick={() => onAba("servico")} className="rounded-full px-4 py-2 text-sm font-medium" style={aba === "servico" ? { backgroundColor: rosa, color: "white" } : { color: "#6b7280" }}>Serviço do atendimento</button>
        <button type="button" onClick={() => onAba("venda")} className="rounded-full px-4 py-2 text-sm font-medium" style={aba === "venda" ? { backgroundColor: rosa, color: "white" } : { color: "#6b7280" }}>Venda de produtos</button>
      </div>
      {aba === "servico" ? <PdvAbaServico {...servico} /> : <PdvAbaVenda {...venda} />}
      {erro && <p className="mt-3 text-sm text-red-600">{erro}</p>}
    </section>
  );
}
