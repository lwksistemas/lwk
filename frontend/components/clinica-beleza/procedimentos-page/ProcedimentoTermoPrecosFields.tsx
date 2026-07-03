import type { ConvenioItem } from "@/lib/clinica-beleza-api";
import {
  FORM_INPUT_CLASS,
  FORM_LABEL_CLASS,
  FORM_SECTION_TITLE_CLASS,
  type ProcedimentoFormState,
} from "./procedimentos-page-types";

interface ProcedimentoTermoFieldsProps {
  form: ProcedimentoFormState;
  accentColor: string;
  onChange: (patch: Partial<ProcedimentoFormState>) => void;
}

export function ProcedimentoTermoFields({ form, accentColor, onChange }: ProcedimentoTermoFieldsProps) {
  return (
    <div className="space-y-4">
      <p className={FORM_SECTION_TITLE_CLASS}>Termo de consentimento</p>
      <label className="flex items-start gap-2.5 cursor-pointer">
        <input
          type="checkbox"
          checked={form.termo_consentimento_ativo}
          onChange={(e) => onChange({ termo_consentimento_ativo: e.target.checked })}
          className="mt-0.5 rounded border-gray-300"
          style={{ accentColor }}
        />
        <span className="text-xs text-gray-600 dark:text-gray-400 leading-snug">
          Exigir termo de consentimento esclarecido (assinatura digital)
        </span>
      </label>
      {form.termo_consentimento_ativo && (
        <div>
          <label className={FORM_LABEL_CLASS}>Texto do termo</label>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
            Variáveis: {"{paciente_nome}"}, {"{paciente_cpf}"}, {"{profissional_nome}"},{" "}
            {"{profissional_conselho}"}, {"{clinica_nome}"}, {"{procedimentos}"}, {"{data}"}
          </p>
          <textarea
            value={form.termo_consentimento}
            onChange={(e) => onChange({ termo_consentimento: e.target.value })}
            rows={10}
            className={`${FORM_INPUT_CLASS} resize-y font-mono text-xs min-h-[180px]`}
          />
        </div>
      )}
    </div>
  );
}

interface ProcedimentoPrecosFieldsProps {
  convenios: ConvenioItem[];
  precosConvenio: Record<number, string>;
  onPrecoChange: (convenioId: number, value: string) => void;
}

export function ProcedimentoPrecosFields({
  convenios,
  precosConvenio,
  onPrecoChange,
}: ProcedimentoPrecosFieldsProps) {
  return (
    <div className="space-y-4">
      <p className={FORM_SECTION_TITLE_CLASS}>Valores por convênio</p>
      {convenios.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {convenios.map((c) => (
            <div key={c.id}>
              <label className={FORM_LABEL_CLASS}>{c.nome}</label>
              <input
                type="text"
                inputMode="decimal"
                value={precosConvenio[c.id] ?? ""}
                onChange={(e) => onPrecoChange(c.id, e.target.value)}
                className={FORM_INPUT_CLASS}
                placeholder="0,00"
              />
              <span className="text-xs text-gray-400 mt-0.5 block">{c.nome}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/20 p-3 rounded-lg">
          Cadastre convênios antes de definir os valores praticados.
        </p>
      )}
    </div>
  );
}
