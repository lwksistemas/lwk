import {
  FORM_INPUT_CLASS,
  FORM_LABEL_CLASS,
  FORM_SECTION_TITLE_CLASS,
  PROTOCOLO_FORM_FIELDS_RIGHT,
  type ProtocoloFormState,
  type ProtocoloFormTextFieldKey,
} from "./protocolos-page-types";

interface ProtocoloEtapasFieldsProps {
  form: ProtocoloFormState;
  onChange: (patch: Partial<ProtocoloFormState>) => void;
}

export function ProtocoloEtapasFields({ form, onChange }: ProtocoloEtapasFieldsProps) {
  return (
    <div className="space-y-4">
      <p className={FORM_SECTION_TITLE_CLASS}>Etapas e cuidados</p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {PROTOCOLO_FORM_FIELDS_RIGHT.map(([key, label]) => (
        <div key={key} className={key === "execucao" ? "lg:col-span-2" : undefined}>
          <label className={FORM_LABEL_CLASS}>{label}</label>
          <textarea
            value={form[key as ProtocoloFormTextFieldKey]}
            onChange={(e) => onChange({ [key]: e.target.value } as Partial<ProtocoloFormState>)}
            rows={key === "execucao" ? 5 : 3}
            className={`${FORM_INPUT_CLASS} resize-y min-h-[72px]`}
            placeholder={label}
          />
        </div>
      ))}
      </div>
    </div>
  );
}
