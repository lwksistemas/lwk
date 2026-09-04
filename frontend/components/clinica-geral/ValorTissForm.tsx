'use client';

type ValorTissFormProps = {
  valor: string;
  onValorChange: (valor: string) => void;
  onSalvarValor: () => void;
  onGerarGuia: () => void;
};

export function ValorTissForm({ valor, onValorChange, onSalvarValor, onGerarGuia }: ValorTissFormProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="mb-3 font-semibold text-slate-800">Valor e TISS</h2>
      <div className="flex flex-wrap items-end gap-2">
        <label className="text-sm">
          Valor (R$)
          <input value={valor} onChange={(e) => onValorChange(e.target.value)} className="ml-2 rounded-md border border-slate-300 px-3 py-2" />
        </label>
        <button type="button" onClick={onSalvarValor} className="rounded-md border px-3 py-2 text-sm">
          Salvar valor
        </button>
        <button type="button" onClick={onGerarGuia} className="rounded-md border px-3 py-2 text-sm">
          Gerar guia TISS
        </button>
      </div>
    </section>
  );
}
