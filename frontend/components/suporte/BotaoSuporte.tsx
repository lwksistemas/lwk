'use client'

import { useState } from 'react'
import ModalChamado from './ModalChamado'

export default function BotaoSuporte() {
  const [modalAberto, setModalAberto] = useState(false)

  return (
    <>
      {/* Botão Flutuante */}
      <button
        onClick={() => setModalAberto(true)}
        className="fixed bottom-6 right-6 z-50 bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-lg transition-all duration-300 hover:scale-110 group"
        title="Abrir Suporte"
      >
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z"
          />
        </svg>
        
        {/* Tooltip */}
        <span className="absolute right-full mr-3 top-1/2 -translate-y-1/2 bg-gray-900 text-white text-sm px-3 py-1 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
          Precisa de ajuda?
        </span>
      </button>

      {/* Modal de Chamado */}
      {modalAberto && (
        <ModalChamado
          aberto={modalAberto}
          onFechar={() => setModalAberto(false)}
        />
      )}
    </>
  )
}
