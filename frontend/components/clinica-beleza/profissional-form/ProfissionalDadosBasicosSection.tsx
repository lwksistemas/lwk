import { formatTelefone, toUpperCase } from "@/lib/format-br";
import { INPUT_CLASS, LABEL_CLASS, type ProfissionalFormState } from "./profissional-form-types";

interface ProfissionalDadosBasicosSectionProps {
  form: ProfissionalFormState;
  onFieldChange: (field: keyof ProfissionalFormState, value: string | boolean) => void;
}

export function ProfissionalDadosBasicosSection({ form, onFieldChange }: ProfissionalDadosBasicosSectionProps) {
  return (
    <section className="bg-white dark:bg-neutral-800 rounded-xl border dark:border-neutral-700 p-5 space-y-4">
      <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Dados Básicos</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className={LABEL_CLASS}>Nome *</label>
          <input
            value={form.name}
            onChange={(e) => onFieldChange("name", toUpperCase(e.target.value))}
            className={INPUT_CLASS}
            placeholder="Nome completo"
          />
        </div>
        <div>
          <label className={LABEL_CLASS}>Especialidade *</label>
          <input
            value={form.specialty}
            onChange={(e) => onFieldChange("specialty", toUpperCase(e.target.value))}
            className={INPUT_CLASS}
            placeholder="Ex.: Esteticista"
          />
        </div>
        <div>
          <label className={LABEL_CLASS}>Telefone</label>
          <input
            value={form.phone}
            onChange={(e) => onFieldChange("phone", formatTelefone(e.target.value))}
            className={INPUT_CLASS}
            placeholder="(00) 00000-0000"
            maxLength={15}
          />
        </div>
        <div>
          <label className={LABEL_CLASS}>E-mail</label>
          <input
            type="email"
            value={form.email}
            onChange={(e) => onFieldChange("email", e.target.value)}
            className={INPUT_CLASS}
            placeholder="email@exemplo.com"
          />
        </div>
      </div>
    </section>
  );
}
