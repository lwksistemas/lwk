import { ChevronDown, ExternalLink, FileText, Layers, PenLine } from "lucide-react";
import type { DocumentoAcao, DocumentoTipo } from "./documentos-types";
import { DOCUMENTO_BUTTONS } from "./documentos-types";

export function DocumentoCriarSection({
  consultaAtiva,
  openDropdown,
  onToggleDropdown,
  onAcao,
}: {
  consultaAtiva: boolean;
  openDropdown: DocumentoTipo | null;
  onToggleDropdown: (tipo: DocumentoTipo) => void;
  onAcao: (tipo: DocumentoTipo, acao: DocumentoAcao) => void;
}) {
  return (
    <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800/80 p-4 md:p-6">
      <div className="flex items-center gap-2 mb-4">
        <FileText size={18} className="text-gray-600 dark:text-gray-400" />
        <h3 className="font-semibold text-gray-900 dark:text-gray-100">Documentos</h3>
      </div>

      {consultaAtiva ? (
        <>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            Crie receituários, pedidos de exame, atestados e outros documentos clínicos para esta consulta.
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {DOCUMENTO_BUTTONS.map((btn) => {
              const Icon = btn.icon;
              const isOpen = openDropdown === btn.tipo;
              return (
                <div key={btn.tipo} className="relative">
                  <button
                    type="button"
                    onClick={() => onToggleDropdown(btn.tipo)}
                    className={`w-full flex items-center justify-center gap-2 px-3 py-3 rounded-lg text-sm font-medium transition-colors border ${
                      isOpen
                        ? "border-[var(--cb-primary)] bg-[var(--cb-primary-light)] text-[var(--cb-primary)]"
                        : "border-gray-200 dark:border-neutral-600 bg-gray-50 dark:bg-neutral-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-neutral-600"
                    }`}
                  >
                    <Icon size={16} />
                    <span className="hidden sm:inline">{btn.label}</span>
                    <span className="sm:hidden">
                      {btn.label.length > 8 ? `${btn.label.slice(0, 6)}…` : btn.label}
                    </span>
                    <ChevronDown size={14} className={`transition-transform ${isOpen ? "rotate-180" : ""}`} />
                  </button>

                  {isOpen && (
                    <div className="absolute top-full left-0 right-0 z-20 mt-1 bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-600 rounded-lg shadow-lg overflow-hidden">
                      {btn.hasMemed && (
                        <button
                          type="button"
                          onClick={() => onAcao(btn.tipo, "memed")}
                          className="w-full flex items-center gap-2 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors"
                        >
                          <ExternalLink size={14} className="text-blue-500" />
                          Usar Memed
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => onAcao(btn.tipo, "template")}
                        className="w-full flex items-center gap-2 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors"
                      >
                        <Layers size={14} className="text-purple-500" />
                        Usar Template
                      </button>
                      <button
                        type="button"
                        onClick={() => onAcao(btn.tipo, "manual")}
                        className="w-full flex items-center gap-2 px-3 py-2.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors"
                      >
                        <PenLine size={14} className="text-green-500" />
                        Digitar Manual
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      ) : (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Documentos só podem ser criados enquanto a consulta está em andamento.
        </p>
      )}
    </div>
  );
}
