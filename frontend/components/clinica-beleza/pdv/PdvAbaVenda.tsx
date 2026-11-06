import type { Dispatch, SetStateAction } from "react";
import { Trash2 } from "lucide-react";
import { createQuickPatient } from "@/hooks/clinica-beleza/criar-agendamento/criar-agendamento-submit-api";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { rosa, type ProdutoOpcao, type VendaLinha } from "./pdv-tipos";

export function PdvAbaVenda({
  onAlternarNovoCliente,
  buscaCliente,
  onBuscaCliente,
  pacienteVenda,
  clientes,
  onEscolherCliente,
  telefoneRecibo,
  onTelefoneRecibo,
  emailRecibo,
  onEmailRecibo,
  novoCliente,
  nomeNovo,
  onNomeNovo,
  telefoneNovo,
  onTelefoneNovo,
  cpfNovo,
  onCpfNovo,
  onClienteCriado,
  buscaProduto,
  onBuscaProduto,
  onEnterProduto,
  sugestoes,
  onAdicionarProduto,
  produtosConsultados,
  linhasVenda,
  setLinhasVenda,
}: {
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
}) {
  return (
    <div className="space-y-4">
      <div>
        <div className="mb-1 flex items-center justify-between">
          <p className="text-xs font-medium text-gray-500">Cliente (opcional)</p>
          <button type="button" className="text-xs font-medium" style={{ color: rosa }} onClick={onAlternarNovoCliente}>Cadastrar cliente</button>
        </div>
        <input value={buscaCliente} onChange={(e) => onBuscaCliente(e.target.value)} placeholder="Nome, ou deixe em branco" className="w-full rounded-xl border px-3 py-2 text-sm" />
        <p className="mt-1 text-xs text-gray-500">{pacienteVenda ? "Cliente cadastrado" : clientes.length > 0 ? "Selecione o cadastro ou continue só com o nome" : buscaCliente.trim().length >= 2 ? "Só o nome, sem cadastro" : buscaCliente.trim() ? "Digite ao menos 2 letras" : "Consumidor não identificado"}</p>
        {clientes.length > 0 && (
          <div className="mt-1 max-h-32 overflow-y-auto rounded-xl border">
            {clientes.map((cliente) => (
              <button key={cliente.id} type="button" className="block w-full px-3 py-2 text-left text-sm hover:bg-gray-50" onClick={() => onEscolherCliente(cliente)}>{cliente.nome}</button>
            ))}
          </div>
        )}
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          <input value={telefoneRecibo} onChange={(e) => onTelefoneRecibo(e.target.value)} placeholder="WhatsApp (opcional)" className="rounded-xl border px-3 py-2 text-sm" />
          <input value={emailRecibo} onChange={(e) => onEmailRecibo(e.target.value)} placeholder="E-mail (opcional)" className="rounded-xl border px-3 py-2 text-sm" />
        </div>
        {novoCliente && (
          <div className="mt-2 grid gap-2 sm:grid-cols-3">
            <input value={nomeNovo} onChange={(e) => onNomeNovo(e.target.value)} placeholder="Nome" className="rounded-xl border px-3 py-2 text-sm" />
            <input value={telefoneNovo} onChange={(e) => onTelefoneNovo(e.target.value)} placeholder="Telefone" className="rounded-xl border px-3 py-2 text-sm" />
            <input value={cpfNovo} onChange={(e) => onCpfNovo(e.target.value)} placeholder="CPF" className="rounded-xl border px-3 py-2 text-sm" />
            <button type="button" className="rounded-xl px-3 py-2 text-sm text-white sm:col-span-3" style={{ backgroundColor: rosa }} onClick={() => void createQuickPatient({ nome: nomeNovo, telefone: telefoneNovo, cpf: cpfNovo }).then((criado) => { onClienteCriado(criado.id, criado.nome || nomeNovo, telefoneNovo); })}>Salvar cadastro</button>
          </div>
        )}
      </div>
      <div>
        <input
          value={buscaProduto}
          onChange={(e) => onBuscaProduto(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && sugestoes.length === 1) {
              e.preventDefault();
              onEnterProduto();
            }
          }}
          placeholder="Produto ou código de barras"
          className="w-full rounded-xl border px-3 py-2 text-sm"
        />
        {sugestoes.length > 0 && (
          <div className="mt-1 max-h-40 overflow-y-auto rounded-xl border">
            {sugestoes.map((produto) => (
              <button key={produto.id} type="button" className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-gray-50" onClick={() => onAdicionarProduto(produto)}>
                <span>{produto.nome}</span>
                <span className="text-gray-500">{formatCurrency(Number(produto.preco_venda || 0))}</span>
              </button>
            ))}
          </div>
        )}
        {produtosConsultados && sugestoes.length === 0 && (
          <p className="mt-1 text-xs text-gray-500">Nenhum produto liberado para venda com esse nome. No cadastro do estoque, marque “Pode vender ao cliente” e informe o preço de venda.</p>
        )}
      </div>
      {linhasVenda.map((linha, indice) => (
        <div key={`${linha.produto}-${indice}`} className="grid grid-cols-[1fr_64px_88px_72px_32px] items-center gap-2">
          <span className="truncate text-sm">{linha.nome}</span>
          <input value={linha.quantidade} onChange={(e) => setLinhasVenda((atual) => atual.map((item, i) => i === indice ? { ...item, quantidade: e.target.value } : item))} className="rounded-xl border px-2 py-2 text-sm" aria-label="Quantidade" />
          <span className="text-sm text-gray-600">{formatCurrency(Number(linha.preco || 0))}</span>
          <input value={linha.desconto} onChange={(e) => setLinhasVenda((atual) => atual.map((item, i) => i === indice ? { ...item, desconto: e.target.value } : item))} className="rounded-xl border px-2 py-2 text-sm" aria-label="Desconto" placeholder="Desc." />
          <button type="button" onClick={() => setLinhasVenda((atual) => atual.filter((_, i) => i !== indice))} aria-label="Remover"><Trash2 size={14} /></button>
        </div>
      ))}
    </div>
  );
}
