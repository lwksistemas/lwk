'use client'

import { useState, useRef, useEffect } from 'react'
import ModalChamado from './ModalChamado'

interface BotaoSuporteProps {
  lojaSlug?: string
  lojaNome?: string
}

export default function BotaoSuporte({ lojaSlug, lojaNome }: BotaoSuporteProps = {}) {
  const [modalAberto, setModalAberto] = useState(false)
  const [position, setPosition] = useState({ bottom: 24, right: 24 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const buttonRef = useRef<HTMLButtonElement>(null)

  // Carregar posição salva do localStorage
  useEffect(() => {
    const saved = localStorage.getItem('botao-suporte-position')
    if (saved) {
      try {
        setPosition(JSON.parse(saved))
      } catch (e) {
        // Ignorar erro de parse
      }
    }
  }, [])

  const handleMouseDown = (e: React.MouseEvent) => {
    // Não iniciar drag se clicar no botão (apenas na borda)
    if ((e.target as HTMLElement).tagName === 'BUTTON') {
      return
    }
    
    setIsDragging(true)
    setDragStart({
      x: e.clientX,
      y: e.clientY
    })
  }

  const handleTouchStart = (e: React.TouchEvent) => {
    const touch = e.touches[0]
    setIsDragging(true)
    setDragStart({
      x: touch.clientX,
      y: touch.clientY
    })
  }

  useEffect(() => {
    if (!isDragging) return

    const handleMove = (e: MouseEvent | TouchEvent) => {
      e.preventDefault()
      
      const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX
      const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY
      
      const deltaX = dragStart.x - clientX
      const deltaY = clientY - dragStart.y
      
      setPosition(prev => {
        const newBottom = Math.max(10, Math.min(window.innerHeight - 70, prev.bottom + deltaY))
        const newRight = Math.max(10, Math.min(window.innerWidth - 150, prev.right + deltaX))
        
        return { bottom: newBottom, right: newRight }
      })
      
      setDragStart({ x: clientX, y: clientY })
    }

    const handleEnd = () => {
      setIsDragging(false)
      // Salvar posição no localStorage
      localStorage.setItem('botao-suporte-position', JSON.stringify(position))
    }

    document.addEventListener('mousemove', handleMove)
    document.addEventListener('mouseup', handleEnd)
    document.addEventListener('touchmove', handleMove, { passive: false })
    document.addEventListener('touchend', handleEnd)

    return () => {
      document.removeEventListener('mousemove', handleMove)
      document.removeEventListener('mouseup', handleEnd)
      document.removeEventListener('touchmove', handleMove)
      document.removeEventListener('touchend', handleEnd)
    }
  }, [isDragging, dragStart, position])

  return (
    <>
      {/* Botão Flutuante - Arrastável */}
      <button
        ref={buttonRef}
        onClick={() => !isDragging && setModalAberto(true)}
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
        className={`fixed z-50 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg transition-all duration-300 flex items-center gap-2 px-5 py-3 ${
          isDragging ? 'cursor-grabbing scale-110' : 'cursor-grab hover:scale-105'
        }`}
        style={{
          bottom: `${position.bottom}px`,
          right: `${position.right}px`,
          touchAction: 'none'
        }}
        title="Arraste para mover | Clique para abrir suporte"
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
        
        {/* Indicador de arrastar (3 pontinhos) */}
        <div className="flex flex-col gap-0.5 ml-1 opacity-50">
          <div className="w-1 h-1 bg-white rounded-full"></div>
          <div className="w-1 h-1 bg-white rounded-full"></div>
          <div className="w-1 h-1 bg-white rounded-full"></div>
        </div>
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
