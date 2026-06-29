import { AlertCircle, CheckCircle2 } from "lucide-react";
import type { NFSeBannerMessage } from "@/components/clinica-beleza/nfse/nfse-form-types";

export function NFSeFormBanner({ message }: { message: NFSeBannerMessage }) {
  return (
    <div
      className={`p-4 rounded-lg flex items-start gap-3 ${
        message.type === "success"
          ? "bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-200"
          : "bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200"
      }`}
    >
      {message.type === "success" ? (
        <CheckCircle2 size={20} className="shrink-0 mt-0.5" />
      ) : (
        <AlertCircle size={20} className="shrink-0 mt-0.5" />
      )}
      <span className="text-sm">{message.text}</span>
    </div>
  );
}
