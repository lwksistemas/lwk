import { AlertCircle, CheckCircle2, Loader2, Upload } from "lucide-react";
import {
  NFSE_CARD_CLASS,
  NFSE_INPUT_CLASS,
  type NFSeConfigSnapshot,
  type NFSeFormData,
  type NFSeTestMessage,
} from "@/components/clinica-beleza/nfse/nfse-form-types";

interface Props {
  formData: NFSeFormData;
  config: NFSeConfigSnapshot | null;
  certificadoFile: File | null;
  issnetTestLoading: boolean;
  issnetTestMessage: NFSeTestMessage | null;
  issnetTestDisabled: boolean;
  onFieldChange: <K extends keyof NFSeFormData>(key: K, value: NFSeFormData[K]) => void;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onTest: () => void;
}

export function NFSeIssnetSection({
  formData,
  config,
  certificadoFile,
  issnetTestLoading,
  issnetTestMessage,
  issnetTestDisabled,
  onFieldChange,
  onFileChange,
  onTest,
}: Props) {
  return (
    <div className={NFSE_CARD_CLASS}>
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Credenciais ISSNet</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Usuário ISSNet *</label>
          <input
            type="text"
            value={formData.issnet_usuario}
            onChange={(e) => onFieldChange("issnet_usuario", e.target.value)}
            className={NFSE_INPUT_CLASS}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Senha ISSNet *</label>
          <input
            type="password"
            value={formData.issnet_senha}
            onChange={(e) => onFieldChange("issnet_senha", e.target.value)}
            placeholder="Digite para alterar"
            className={NFSE_INPUT_CLASS}
          />
        </div>
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
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Senha do Certificado *
          </label>
          <input
            type="password"
            value={formData.issnet_senha_certificado}
            onChange={(e) => onFieldChange("issnet_senha_certificado", e.target.value)}
            placeholder="Senha do arquivo .pfx"
            className={NFSE_INPUT_CLASS}
          />
        </div>
        <div className="md:col-span-2 space-y-3 pt-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.issnet_ambiente_homologacao}
              onChange={(e) => onFieldChange("issnet_ambiente_homologacao", e.target.checked)}
              className="w-4 h-4"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">Homologação / teste (ISSNet)</span>
          </label>
          <button
            type="button"
            onClick={() => void onTest()}
            disabled={issnetTestDisabled}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-[#0176d3] text-[#0176d3] hover:bg-[#0176d3]/10 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {issnetTestLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Testando…
              </>
            ) : (
              "Testar conexão ISSNet"
            )}
          </button>
          {issnetTestMessage && (
            <div
              className={`flex items-start gap-2 p-3 rounded-lg text-sm ${
                issnetTestMessage.type === "ok"
                  ? "bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200 border border-green-200"
                  : "bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 border border-red-200"
              }`}
            >
              {issnetTestMessage.type === "ok" ? (
                <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              )}
              <span>{issnetTestMessage.text}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
