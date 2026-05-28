'use client';

export function NfseLojaLoading() {
  return (
    <div className="text-center py-12">
      <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-[#0176d3]" />
      <p className="mt-2 text-gray-600 dark:text-gray-400">Carregando...</p>
    </div>
  );
}
