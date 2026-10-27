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
    <details className="group">
      <summary className={`${FORM_SECTION_TITLE_CLASS} cursor-pointer list-none [&::-webkit-details-marker]:hidden`}>
        Etapas e cuidados
      </summary>
      <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
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
    </details>
  );
}
