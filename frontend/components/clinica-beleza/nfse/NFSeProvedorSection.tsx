import {
  NFSE_CARD_CLASS,
  type NFSeFormData,
} from "@/components/clinica-beleza/nfse/nfse-form-types";
import {
  NFSE_EMISSAO_OPCOES,
  aplicarEmissaoOpcao,
  resolverEmissaoOpcao,
  type EmissaoOpcao,
} from "@/lib/nfse-emissao-opcoes";

interface Props {
  formData: NFSeFormData;
  onApply: (patch: Partial<NFSeFormData>) => void;
}

export function NFSeProvedorSection({ formData, onApply }: Props) {
  const selected = resolverEmissaoOpcao(
    formData.provedor_nf,
    formData.issnet_usar_padrao_nacional,
  );

  const selecionar = (opcao: EmissaoOpcao) => {
    onApply(aplicarEmissaoOpcao(opcao));
  };

  return (
    <div className={NFSE_CARD_CLASS}>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
        Como deseja emitir?
      </h2>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        Mesmas opções do CRM Vendas. Selecione e configure o emissor abaixo.
      </p>
      <div className="space-y-3">
        {NFSE_EMISSAO_OPCOES.map((op) => {
          const isSelected = selected === op.key;
          return (
            <label
              key={op.key}
              className={`flex items-start gap-3 p-4 rounded-lg border-2 cursor-pointer transition-all ${
                isSelected
                  ? "border-[#0176d3] bg-[#e3f3ff] dark:bg-[#0176d3]/10"
                  : "border-gray-200 dark:border-[#0d1f3c] hover:border-gray-300"
              }`}
            >
              <input
                type="radio"
                name="emissao_opcao"
                value={op.key}
                checked={isSelected}
                onChange={() => selecionar(op.key)}
                className="mt-1"
              />
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold text-[#0176d3] tabular-nums">
                    {op.numero}.
                  </span>
                  <span className="font-medium text-gray-900 dark:text-white">{op.titulo}</span>
                  {op.badge ? (
                    <span className="text-[10px] uppercase tracking-wide px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                      {op.badge}
                    </span>
                  ) : null}
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{op.descricao}</p>
              </div>
            </label>
          );
        })}
      </div>
    </div>
  );
}
