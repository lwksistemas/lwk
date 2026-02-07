'use client'

import { useState } from 'react'
import ModalChamado from './ModalChamado'

interface BotaoSuporteProps {
  lojaSlug?: string
  lojaNome?: string
}

export default function BotaoSuporte({ lojaSlug, lojaNome }: BotaoSuporteProps = {}) {
  const [modalAberto, setModalAberto] = useState(false)

  return (
    <>
      {/* Botão Flutuante - Melhorado */}
      <button
        onClick={() => setModalAberto(true)}
        className="fixed bottom-6 right-6 z-50 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg transition-all duration-300 hover:scale-105 group flex items-center gap-2 px-5 py-3"
        title="Abrir Suporte"
      >
        {/* Ícone de Headset/Microfone */}
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
            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
          />
        </svg>
        
        {/* Texto "Suporte" */}
        <span className="font-semibold text-sm">Suporte</span>
        
        {/* Badge de notificação (opcional - pode ser usado no futuro) */}
        {/* <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
          3
        </span> */}
      </button>

      {/* Modal de Chamado */}
      {modalAberto && (
        <ModalChamado
          aberto={modalAberto}
          onFechar={() => setModalAberto(false)}
          lojaSlug={lojaSlug}
          lojaNome={lojaNome}
        />
      )}
    </>
  )
}
