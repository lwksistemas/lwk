import type { ConvenioItem } from "@/lib/clinica-beleza-api";
import {
  FORM_INPUT_CLASS,
  FORM_LABEL_CLASS,
  FORM_SECTION_TITLE_CLASS,
} from "./procedimentos-page-types";

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
