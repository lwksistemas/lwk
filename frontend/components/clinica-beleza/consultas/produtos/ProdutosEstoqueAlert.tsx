import { AlertTriangle } from "lucide-react";

export function ProdutosEstoqueAlert({ mensagens }: { mensagens: string[] }) {
  if (!mensagens.length) return null;

  return (
    <div className="flex gap-2 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200 text-sm">
      <AlertTriangle size={18} className="shrink-0 mt-0.5" />
      <div>
        <p className="font-medium">Estoque insuficiente — a consulta não poderá ser finalizada:</p>
        <ul className="mt-1 list-disc list-inside space-y-0.5">
          {mensagens.map((msg) => (
            <li key={msg}>{msg}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
