import { Upload } from "lucide-react";
import {
  NFSE_CARD_CLASS,
  NFSE_INPUT_CLASS,
  type NFSeConfigSnapshot,
  type NFSeFormData,
} from "@/components/clinica-beleza/nfse/nfse-form-types";

interface Props {
  formData: NFSeFormData;
  config: NFSeConfigSnapshot | null;
  certificadoFile: File | null;
  onFieldChange: <K extends keyof NFSeFormData>(key: K, value: NFSeFormData[K]) => void;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export function NFSeNacionalAdnSection({
  formData,
  config,
  certificadoFile,
  onFieldChange,
  onFileChange,
}: Props) {
  return (
    <div className={NFSE_CARD_CLASS}>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
        Configurações — API Nacional NFS-e
      </h2>
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
        Emissão direta (ADN/SEFIN). Requer certificado A1 e município habilitado.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Certificado Digital A1 (.pfx) *
          </label>
          <label className="flex items-center gap-3 px-4 py-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:border-[#0176d3] transition-colors">
            <Upload size={20} className="text-gray-400" />
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {certificadoFile
                ? certificadoFile.name
                : config?.issnet_certificado
                  ? "Certificado já enviado - Clique para alterar"
                  : "Clique para selecionar o arquivo .pfx"}
            </span>
            <input type="file" accept=".pfx" onChange={onFileChange} className="hidden" />
          </label>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Senha do certificado *
          </label>
          <input
            type="password"
            value={formData.issnet_senha_certificado}
            onChange={(e) => onFieldChange("issnet_senha_certificado", e.target.value)}
            placeholder="Senha do .pfx"
            className={NFSE_INPUT_CLASS}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Código IBGE do município *
          </label>
          <input
            type="text"
            inputMode="numeric"
            maxLength={7}
            value={formData.nacional_codigo_municipio}
            onChange={(e) =>
              onFieldChange("nacional_codigo_municipio", e.target.value.replace(/\D/g, "").slice(0, 7))
            }
            placeholder="3543402"
            className={NFSE_INPUT_CLASS}
          />
          <p className="text-[11px] text-gray-500 mt-1">Ex.: 3543402 Ribeirão Preto</p>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Inscrição municipal *
          </label>
          <input
            type="text"
            value={formData.inscricao_municipal}
            onChange={(e) => onFieldChange("inscricao_municipal", e.target.value)}
            className={NFSE_INPUT_CLASS}
          />
        </div>
      </div>
    </div>
  );
}
