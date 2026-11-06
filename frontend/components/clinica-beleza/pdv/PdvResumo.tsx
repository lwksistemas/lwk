import Link from "next/link";
import { DollarSign, PenLine } from "lucide-react";
import { EnviarReciboAssinaturaAcao } from "@/components/clinica-beleza/consultas/receber/EnviarReciboAssinaturaAcao";
import { ReceberReciboActions } from "@/components/clinica-beleza/consultas/receber/ReceberReciboActions";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { FORMAS_PDV } from "./pdv-utils";
import { rosa } from "./pdv-tipos";

export function PdvResumo({
  subtotal,
  aba,
  editandoDesconto,
  desconto,
  onDesconto,
  onEditarDesconto,
  descontoNum,
  pago,
  total,
  vendaAPrazo,
  slug,
  atendimentoIsento,
  aguardandoChegada,
  forma,
  onForma,
  caixaAberto,
  mostrarFormas,
  formasExibidas,
  quitado,
  consultaFinalizada,
  salvando,
  consultaId,
  onReceberServico,
  onReceberVenda,
  mostrarRecibo,
  paymentRecibo,
  onImprimirRecibo,
  onEnviarRecibo,
}: {
  subtotal: number;
  aba: "servico" | "venda";
  editandoDesconto: boolean;
  desconto: string;
  onDesconto: (valor: string) => void;
  onEditarDesconto: (aberto: boolean) => void;
  descontoNum: number;
  pago: number;
  total: number;
  vendaAPrazo: boolean;
  slug: string;
  atendimentoIsento: boolean;
  aguardandoChegada: boolean;
  forma: string;
  onForma: (valor: string) => void;
  caixaAberto: boolean;
  mostrarFormas: boolean;
  formasExibidas: { id: number; rotulo: string; valor: number }[];
  quitado: boolean;
  consultaFinalizada: boolean;
  salvando: boolean;
  consultaId?: number;
  onReceberServico: () => void;
  onReceberVenda: () => void;
  mostrarRecibo: boolean;
  paymentRecibo: number;
  onImprimirRecibo: () => void;
  onEnviarRecibo: (canal: "email" | "whatsapp") => void;
}) {
  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-4">
      <h2 className="mb-3 font-semibold text-gray-900">Resumo e pagamento</h2>
      <div className="space-y-2 text-sm">
        <div className="flex justify-between"><span className="text-gray-500">Subtotal</span><span>{formatCurrency(subtotal)}</span></div>
        <div className="flex justify-between">
          <span className="text-gray-500">Desconto</span>
          {aba === "venda" && editandoDesconto ? (
            <input autoFocus value={desconto} onChange={(e) => onDesconto(e.target.value)} onBlur={() => onEditarDesconto(false)} className="w-24 rounded border px-2 py-1 text-right text-sm" />
          ) : aba === "venda" ? (
            <button type="button" className="inline-flex items-center gap-1" onClick={() => onEditarDesconto(true)}>{formatCurrency(descontoNum)} <PenLine size={12} /></button>
          ) : (
            <span>{formatCurrency(descontoNum)}</span>
          )}
        </div>
        {pago > 0.009 && aba === "servico" && <div className="flex justify-between"><span className="text-gray-500">Já recebido</span><span>{formatCurrency(pago)}</span></div>}
      </div>
      <div className="my-4 flex items-center justify-between rounded-xl bg-pink-50 px-3 py-3">
        <span className="text-sm font-medium" style={{ color: rosa }}>Total a receber</span>
        <span className="text-lg font-semibold" style={{ color: rosa }}>{formatCurrency(total)}</span>
      </div>
      {vendaAPrazo ? (
        <p className="mb-4 rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-800">
          Esta venda está a prazo. O recebimento fica no{" "}
          <Link href={`/loja/${slug}/clinica-beleza/financeiro`} className="font-medium underline">Financeiro</Link>.
        </p>
      ) : atendimentoIsento ? (
        <p className="mb-4 rounded-xl bg-sky-50 px-3 py-2 text-sm text-sky-800">Retorno isento. Sem valor a receber.</p>
      ) : aguardandoChegada ? (
        <p className="mb-4 rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-800">
          A cliente ainda não chegou. Marque como presente para o caixa receber.
        </p>
      ) : aba === "venda" ? (
        <>
          <label className="mb-1 block text-sm text-gray-600">Forma de pagamento</label>
          <select value={forma} onChange={(e) => onForma(e.target.value)} className="mb-3 w-full rounded-xl border px-3 py-2 text-sm">
            {FORMAS_PDV.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
          </select>
        </>
      ) : null}
      {!vendaAPrazo && !atendimentoIsento && !aguardandoChegada && !caixaAberto && (
        <p className="mb-3 rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-800">Abra o caixa para vender ou receber um atendimento.</p>
      )}
      {mostrarFormas && (
        <div className="mb-3 space-y-2">
          <p className="text-sm text-gray-600">Formas de pagamento</p>
          {formasExibidas.map((linha) => (
            <div key={linha.id} className="flex items-center justify-between rounded-xl border px-3 py-2 text-sm">
              <span>{linha.rotulo}</span>
              <strong>{formatCurrency(linha.valor)}</strong>
            </div>
          ))}
          {quitado && !consultaFinalizada && (
            <p className="rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-800">
              Pagamento registrado. O recibo só pode ser impresso ou enviado depois de finalizar o atendimento.
            </p>
          )}
        </div>
      )}
      {!vendaAPrazo && !atendimentoIsento && !aguardandoChegada && !(aba === "servico" && quitado) && (
        <button
          type="button"
          disabled={salvando || !caixaAberto || (aba === "venda" ? total <= 0 : (!consultaId || total <= 0))}
          onClick={() => {
            if (aba === "servico") {
              onReceberServico();
              return;
            }
            onReceberVenda();
          }}
          className="mb-4 flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-semibold text-white disabled:opacity-50"
          style={{ backgroundColor: rosa }}
        >
          <DollarSign size={16} /> {salvando ? "Recebendo..." : "Receber pagamento"}
        </button>
      )}
      {mostrarRecibo && paymentRecibo > 0 && (
        <div className="space-y-3">
          <ReceberReciboActions
            onImprimir={onImprimirRecibo}
            onEmail={() => onEnviarRecibo("email")}
            onWhatsApp={() => onEnviarRecibo("whatsapp")}
          />
          {vendaAPrazo && <EnviarReciboAssinaturaAcao paymentId={paymentRecibo} />}
        </div>
      )}
    </section>
  );
}
