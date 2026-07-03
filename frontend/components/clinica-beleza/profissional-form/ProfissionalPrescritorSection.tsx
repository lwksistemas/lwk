import { formatCpf } from "@/lib/format-br";
import {
  CONSELHOS,
  INPUT_CLASS,
  LABEL_CLASS,
  UFS_BR,
  type ProfissionalFormState,
} from "./profissional-form-types";

interface ProfissionalPrescritorSectionProps {
  form: ProfissionalFormState;
  onFieldChange: (field: keyof ProfissionalFormState, value: string | boolean) => void;
}

export function ProfissionalPrescritorSection({ form, onFieldChange }: ProfissionalPrescritorSectionProps) {
  return (
    <section className="bg-white dark:bg-neutral-800 rounded-xl border dark:border-neutral-700 p-5 space-y-4">
      <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Prescritor (Memed)</h3>
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
        <div className="col-span-3 sm:col-span-2">
          <label className={LABEL_CLASS}>Conselho</label>
          <select
            value={form.conselho}
            onChange={(e) => onFieldChange("conselho", e.target.value)}
            className={INPUT_CLASS}
          >
            <option value="">—</option>
            {CONSELHOS.map(([v, l]) => (
              <option key={v} value={v}>{l}</option>
            ))}
          </select>
        </div>
        <div className="col-span-2 sm:col-span-2">
          <label className={LABEL_CLASS}>Nº registro</label>
          <input
            value={form.registro}
            onChange={(e) => onFieldChange("registro", e.target.value)}
            className={INPUT_CLASS}
            placeholder="016964"
          />
        </div>
        <div className="col-span-1 sm:col-span-2">
          <label className={LABEL_CLASS}>UF</label>
          <select value={form.uf} onChange={(e) => onFieldChange("uf", e.target.value)} className={INPUT_CLASS}>
            <option value="">—</option>
            {UFS_BR.map((uf) => (
              <option key={uf} value={uf}>{uf}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className={LABEL_CLASS}>CPF</label>
          <input
            value={form.cpf}
            onChange={(e) => onFieldChange("cpf", formatCpf(e.target.value))}
            className={INPUT_CLASS}
            placeholder="000.000.000-00"
            maxLength={14}
          />
        </div>
        <div>
          <label className={LABEL_CLASS}>Data de nascimento</label>
          <input
            type="date"
            value={form.data_nascimento}
            onChange={(e) => onFieldChange("data_nascimento", e.target.value)}
            className={INPUT_CLASS}
          />
        </div>
        <div>
          <label className={LABEL_CLASS}>Sexo</label>
          <select value={form.sexo} onChange={(e) => onFieldChange("sexo", e.target.value)} className={INPUT_CLASS}>
            <option value="">—</option>
            <option value="M">Masculino</option>
            <option value="F">Feminino</option>
          </select>
        </div>
      </div>
    </section>
  );
}
