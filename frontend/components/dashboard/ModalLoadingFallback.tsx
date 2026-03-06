'use client';

/** Fallback de loading para modais (lazy). Usado por clinica-estetica, etc. */
export function ModalLoadingFallback() {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-8 shadow-2xl">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" aria-hidden />
          <span className="text-gray-700 dark:text-gray-300">Carregando...</span>
        </div>
      </div>
    </div>
  );
}
