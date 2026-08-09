'use client';

import { AlertCircle, CheckCircle } from 'lucide-react';

export function FotoPublicaLoading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <p className="text-gray-600">Carregando…</p>
    </div>
  );
}

export function FotoPublicaSucesso({ fotosEnviadas }: { fotosEnviadas: number }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-green-50 p-4">
      <div className="bg-white rounded-2xl shadow-lg p-8 max-w-sm w-full text-center">
        <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
        <h1 className="text-xl font-bold text-gray-900 mb-2">
          {fotosEnviadas === 1 ? 'Foto registrada!' : `${fotosEnviadas} fotos registradas!`}
        </h1>
        <p className="text-gray-600 text-sm">
          A imagem já aparece na consulta no computador.
          <br />
          <span className="text-gray-500">Fechando esta página…</span>
        </p>
        <p className="text-xs text-gray-400 mt-4">
          Para enviar outra foto, escaneie o QR novamente na consulta.
        </p>
      </div>
    </div>
  );
}

export function FotoPublicaErro({ erro }: { erro: string }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-red-50 p-4">
      <div className="bg-white rounded-2xl shadow-lg p-8 max-w-sm w-full text-center">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
        <p className="text-gray-800">{erro}</p>
      </div>
    </div>
  );
}
