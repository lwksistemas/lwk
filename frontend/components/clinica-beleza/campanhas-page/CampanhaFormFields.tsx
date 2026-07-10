import { CLINICA_FORM_INPUT } from "@/hooks/clinica-beleza";
import { toUpperCase } from "@/lib/format-br";
import type { CampanhaFormState } from "./campanhas-page-types";

interface CampanhaFormFieldsProps {
  form: CampanhaFormState;
  onChange: (patch: Partial<CampanhaFormState>) => void;
}

export function CampanhaFormFields({ form, onChange }: CampanhaFormFieldsProps) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Título da promoção *
        </label>
        <input
          value={form.titulo}
          onChange={(e) => onChange({ titulo: toUpperCase(e.target.value) })}
          className={CLINICA_FORM_INPUT}
          placeholder="Ex: Black Friday - 30% off"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Mensagem (WhatsApp) *
        </label>
        <textarea
          value={form.mensagem}
          onChange={(e) => onChange({ mensagem: e.target.value })}
          rows={6}
          className={`${CLINICA_FORM_INPUT} resize-none`}
          placeholder="Texto que será enviado para os pacientes..."
        />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Vigência início
          </label>
          <input
            type="date"
            value={form.data_inicio}
            onChange={(e) => onChange({ data_inicio: e.target.value })}
            className={CLINICA_FORM_INPUT}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Vigência fim
          </label>
          <input
            type="date"
            value={form.data_fim}
            onChange={(e) => onChange({ data_fim: e.target.value })}
            className={CLINICA_FORM_INPUT}
          />
        </div>
      </div>
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={form.ativa}
          onChange={(e) => onChange({ ativa: e.target.checked })}
          className="rounded border-gray-300 dark:border-neutral-600"
          style={{ accentColor: 'var(--cb-primary, #8B3D52)' }}
        />
        <span className="text-sm text-gray-700 dark:text-gray-300">Campanha ativa</span>
      </label>
    </div>
  );
}
