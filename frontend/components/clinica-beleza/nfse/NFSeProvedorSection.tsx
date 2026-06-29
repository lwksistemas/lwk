import {
  NFSE_CARD_CLASS,
  NFSE_PROVEDOR_INFO,
  type NFSeFormData,
  type NFSeProvedor,
} from "@/components/clinica-beleza/nfse/nfse-form-types";

interface Props {
  provedor: NFSeProvedor;
  onChange: (provedor: NFSeProvedor) => void;
}

export function NFSeProvedorSection({ provedor, onChange }: Props) {
  return (
    <div className={NFSE_CARD_CLASS}>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Provedor de Nota Fiscal</h2>
      <div className="space-y-3">
        {(Object.keys(NFSE_PROVEDOR_INFO) as NFSeProvedor[]).map((key) => {
          const info = NFSE_PROVEDOR_INFO[key];
          const isDisabled = key === "nacional";
          return (
            <label
              key={key}
              className={`flex items-start gap-3 p-4 rounded-lg border-2 cursor-pointer transition-all ${
                provedor === key
                  ? "border-[#0176d3] bg-[#e3f3ff] dark:bg-[#0176d3]/10"
                  : "border-gray-200 dark:border-[#0d1f3c] hover:border-gray-300"
              } ${isDisabled ? "opacity-50 cursor-not-allowed" : ""}`}
            >
              <input
                type="radio"
                name="provedor_nf"
                value={key}
                checked={provedor === key}
                onChange={(e) => onChange(e.target.value as NFSeFormData["provedor_nf"])}
                disabled={isDisabled}
                className="mt-1"
              />
              <div className="flex-1">
                <div className="font-medium text-gray-900 dark:text-white">
                  {info.titulo}
                  {isDisabled && <span className="ml-2 text-xs text-gray-500">(Em breve)</span>}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">{info.descricao}</div>
              </div>
            </label>
          );
        })}
      </div>
    </div>
  );
}
