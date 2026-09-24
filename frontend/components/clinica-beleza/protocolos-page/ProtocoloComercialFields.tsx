import { Plus, Trash2 } from "lucide-react";
import {
  FORM_INPUT_CLASS,
  FORM_LABEL_CLASS,
  FORM_SECTION_TITLE_CLASS,
  type ProtocoloFormState,
  type ProtocoloProdutoOption,
} from "./protocolos-page-types";

interface ProtocoloComercialFieldsProps {
  form: ProtocoloFormState;
  onChange: (patch: Partial<ProtocoloFormState>) => void;
}

export function ProtocoloComercialFields({ form, onChange }: ProtocoloComercialFieldsProps) {
  return (
    <div className="space-y-4">
      <p className={FORM_SECTION_TITLE_CLASS}>Pacote comercial</p>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label className={FORM_LABEL_CLASS}>Sessões *</label>
          <input
            type="number"
            min={1}
            value={form.sessoes}
            onChange={(e) => onChange({ sessoes: e.target.value })}
            className={FORM_INPUT_CLASS}
          />
        </div>
        <div>
          <label className={FORM_LABEL_CLASS}>Intervalo entre sessões *</label>
          <input
            type="number"
            min={1}
            value={form.intervalo_quantidade}
            onChange={(e) => onChange({ intervalo_quantidade: e.target.value })}
            className={FORM_INPUT_CLASS}
          />
        </div>
        <div>
          <label className={FORM_LABEL_CLASS}>Unidade *</label>
          <select
            value={form.intervalo_unidade}
            onChange={(e) =>
              onChange({ intervalo_unidade: e.target.value as ProtocoloFormState["intervalo_unidade"] })
            }
            className={FORM_INPUT_CLASS}
          >
            <option value="dias">Dias</option>
            <option value="semanas">Semanas</option>
            <option value="meses">Meses</option>
          </select>
        </div>
      </div>
      <p className="text-xs text-gray-500">
        O intervalo é entre uma sessão e a outra. Quatro sessões a cada 7 dias ocupam 21 dias.
        O preço do pacote é o valor do procedimento, por convênio, na página Procedimentos.
      </p>
    </div>
  );
}

interface ProtocoloProdutosFieldsProps {
  form: ProtocoloFormState;
  produtos: ProtocoloProdutoOption[];
  onChange: (patch: Partial<ProtocoloFormState>) => void;
}

export function ProtocoloProdutosFields({ form, produtos, onChange }: ProtocoloProdutosFieldsProps) {
  const atualizarLinha = (indice: number, patch: Partial<ProtocoloFormState["produtos"][number]>) => {
    const linhas = form.produtos.map((linha, i) => (i === indice ? { ...linha, ...patch } : linha));
    onChange({ produtos: linhas });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <p className={FORM_SECTION_TITLE_CLASS}>Produtos por sessão</p>
        <button
          type="button"
          onClick={() => onChange({ produtos: [...form.produtos, { produto: "", quantidade: "1" }] })}
          className="inline-flex items-center gap-1 text-sm font-medium"
          style={{ color: "var(--cb-primary, #8B3D52)" }}
        >
          <Plus size={16} />
          Produto
        </button>
      </div>
      {form.produtos.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhum produto. O estoque só é baixado quando a consulta é finalizada.</p>
      ) : (
        <div className="space-y-3">
          {form.produtos.map((linha, indice) => (
            <div key={`${indice}-${linha.produto}`} className="grid grid-cols-1 sm:grid-cols-[1fr_180px_auto] gap-3 items-end">
              <div>
                <label className={FORM_LABEL_CLASS}>Produto</label>
                <select
                  value={linha.produto}
                  onChange={(e) => atualizarLinha(indice, { produto: e.target.value })}
                  className={FORM_INPUT_CLASS}
                >
                  <option value="">Selecione...</option>
                  {produtos.map((produto) => (
                    <option key={produto.id} value={produto.id}>
                      {produto.nome}
                      {produto.unidade_medida ? ` (${produto.unidade_medida})` : ""}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className={FORM_LABEL_CLASS}>Qtd. por sessão</label>
                <input
                  inputMode="decimal"
                  value={linha.quantidade}
                  onChange={(e) => atualizarLinha(indice, { quantidade: e.target.value })}
                  className={FORM_INPUT_CLASS}
                />
              </div>
              <button
                type="button"
                onClick={() => onChange({ produtos: form.produtos.filter((_, i) => i !== indice) })}
                className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                title="Remover produto"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
