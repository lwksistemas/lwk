import { CalendarDays, Check, DollarSign, Package, Users } from "lucide-react";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { Indicador } from "./PdvPecas";

export function PdvIndicadores({
  agendamentos,
  presentes,
  aReceber,
  recebidoHoje,
  vendasProdutos,
}: {
  agendamentos: number;
  presentes: number;
  aReceber: number;
  recebidoHoje: number;
  vendasProdutos: number;
}) {
  return (
    <div className="mb-4 grid grid-cols-2 gap-3 xl:grid-cols-5">
      <Indicador icone={<CalendarDays size={16} />} cor="bg-pink-50 text-pink-600" titulo="Agendamentos hoje" valor={String(agendamentos)} />
      <Indicador icone={<Users size={16} />} cor="bg-sky-50 text-sky-600" titulo="Presentes" valor={String(presentes)} />
      <Indicador icone={<DollarSign size={16} />} cor="bg-pink-50 text-pink-600" titulo="A receber" valor={formatCurrency(aReceber)} />
      <Indicador icone={<Check size={16} />} cor="bg-emerald-50 text-emerald-600" titulo="Recebido hoje" valor={formatCurrency(recebidoHoje)} />
      <Indicador icone={<Package size={16} />} cor="bg-violet-50 text-violet-600" titulo="Vendas de produtos" valor={formatCurrency(vendasProdutos)} />
    </div>
  );
}
