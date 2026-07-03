import { suggestUsernameFromName } from "./profissional-form-utils";
import { INPUT_CLASS, LABEL_CLASS, type ProfissionalFormState } from "./profissional-form-types";

interface ProfissionalAcessoSectionProps {
  form: ProfissionalFormState;
  onFieldChange: (field: keyof ProfissionalFormState, value: string | boolean) => void;
}

export function ProfissionalAcessoSection({ form, onFieldChange }: ProfissionalAcessoSectionProps) {
  return (
    <section className="bg-white dark:bg-neutral-800 rounded-xl border dark:border-neutral-700 p-5 space-y-4">
      <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Acesso ao sistema</h3>
      <div>
        <label className={LABEL_CLASS}>Perfil de permissão</label>
        <select
          value={form.perfil}
          onChange={(e) => onFieldChange("perfil", e.target.value)}
          className={INPUT_CLASS}
        >
          <option value="administrador">Administrador</option>
          <option value="profissional">Profissional</option>
          <option value="recepcionista">Recepcionista</option>
          <option value="caixa">Caixa</option>
          <option value="estoque">Estoque</option>
        </select>
      </div>
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={form.criar_acesso}
          onChange={(e) => {
            onFieldChange("criar_acesso", e.target.checked);
            if (e.target.checked && !form.username) {
              onFieldChange("username", suggestUsernameFromName(form.name));
            }
          }}
          className="rounded border-gray-300 dark:border-neutral-600 text-purple-600"
        />
        <span className="text-sm text-gray-700 dark:text-gray-300">Criar login e enviar senha por e-mail</span>
      </label>
      {form.criar_acesso && (
        <div className="space-y-3 pt-2 pl-6 border-l-2 border-purple-200 dark:border-purple-800">
          <div>
            <label className={LABEL_CLASS}>Usuário para login *</label>
            <input
              type="text"
              value={form.username}
              onChange={(e) =>
                onFieldChange("username", e.target.value.toLowerCase().replace(/[^a-z0-9._-]/g, ""))
              }
              className={INPUT_CLASS}
              placeholder="Ex: daniel, maria.silva"
            />
            <p className="text-xs text-gray-500 mt-1">
              Será usado para entrar no sistema (sem espaços ou caracteres especiais)
            </p>
          </div>
          <div>
            <label className={LABEL_CLASS}>E-mail (para envio da senha) *</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => onFieldChange("email", e.target.value)}
              className={INPUT_CLASS}
              placeholder="email@exemplo.com"
            />
          </div>
        </div>
      )}
    </section>
  );
}
