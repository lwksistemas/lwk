import { MapPin } from "lucide-react";
import { toUpperCase } from "@/lib/format-br";
import { isCepCompleto } from "./paciente-cadastro-utils";
import { FieldLabel, FORM_SELECT_CLASS, SECTION_TITLE_CLASS } from "./paciente-cadastro-ui";
import { UF_LIST, type PacienteFormState } from "./paciente-cadastro-types";

interface PacienteEnderecoSectionProps {
  form: PacienteFormState;
  buscarCepLoading: boolean;
  accentColor: string;
  onChange: (patch: Partial<PacienteFormState>) => void;
  onCepChange: (value: string) => void;
  onBuscarCep: () => void;
}

export function PacienteEnderecoSection({
  form,
  buscarCepLoading,
  accentColor,
  onChange,
  onCepChange,
  onBuscarCep,
}: PacienteEnderecoSectionProps) {
  return (
    <div className="space-y-4">
      <p className={SECTION_TITLE_CLASS}>Endereço</p>

      <div>
        <FieldLabel>Logradouro</FieldLabel>
        <div className="relative">
          <MapPin
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none"
            aria-hidden
          />
          <input
            value={form.logradouro}
            onChange={(e) => onChange({ logradouro: toUpperCase(e.target.value) })}
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800"
            placeholder="Rua, avenida..."
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <div className="w-[120px]">
          <FieldLabel>CEP</FieldLabel>
          <input
            type="text"
            value={form.cep}
            onChange={(e) => onCepChange(e.target.value)}
            onBlur={() => isCepCompleto(form.cep) && onBuscarCep()}
            maxLength={9}
            className={FORM_SELECT_CLASS}
            placeholder="00000-000"
            inputMode="numeric"
          />
        </div>
        <div className="flex items-end">
          <button
            type="button"
            onClick={onBuscarCep}
            disabled={buscarCepLoading || !isCepCompleto(form.cep)}
            className="px-3 py-2 rounded-lg border text-sm font-medium disabled:opacity-50 whitespace-nowrap"
            style={{ borderColor: accentColor, color: accentColor }}
          >
            {buscarCepLoading ? "..." : "Consultar CEP"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div>
          <FieldLabel>Número</FieldLabel>
          <input
            value={form.numero}
            onChange={(e) => onChange({ numero: e.target.value })}
            className={FORM_SELECT_CLASS}
            placeholder="Nº"
          />
        </div>
        <div className="col-span-1 sm:col-span-3">
          <FieldLabel>Complemento</FieldLabel>
          <input
            value={form.complemento}
            onChange={(e) => onChange({ complemento: toUpperCase(e.target.value) })}
            className={FORM_SELECT_CLASS}
            placeholder="Opcional"
          />
        </div>
        <div className="col-span-2 sm:col-span-2">
          <FieldLabel>Bairro</FieldLabel>
          <input
            value={form.bairro}
            onChange={(e) => onChange({ bairro: toUpperCase(e.target.value) })}
            className={FORM_SELECT_CLASS}
            placeholder="Bairro"
          />
        </div>
        <div>
          <FieldLabel>Cidade</FieldLabel>
          <input
            value={form.cidade}
            onChange={(e) => onChange({ cidade: toUpperCase(e.target.value) })}
            className={FORM_SELECT_CLASS}
            placeholder="Cidade"
          />
        </div>
        <div>
          <FieldLabel>UF</FieldLabel>
          <select
            value={form.uf}
            onChange={(e) => onChange({ uf: e.target.value })}
            className={FORM_SELECT_CLASS}
          >
            <option value="">—</option>
            {UF_LIST.map((uf) => (
              <option key={uf} value={uf}>
                {uf}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <FieldLabel>Observações</FieldLabel>
        <textarea
          value={form.notes}
          onChange={(e) => onChange({ notes: e.target.value })}
          rows={3}
          className={`${FORM_SELECT_CLASS} resize-y min-h-[72px]`}
          placeholder="Opcional"
        />
      </div>
    </div>
  );
}
