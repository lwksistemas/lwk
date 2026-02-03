import { useState, useCallback, useMemo } from 'react';

type ModalState<T extends string> = Record<T, boolean>;

interface UseModalsReturn<T extends string> {
  modals: ModalState<T>;
  openModal: (name: T) => void;
  closeModal: (name: T) => void;
  toggleModal: (name: T) => void;
  closeAll: () => void;
  isOpen: (name: T) => boolean;
}

/**
 * Hook customizado para gerenciar múltiplos modais.
 * Simplifica o gerenciamento de estado de modais em dashboards.
 * 
 * @example
 * const { modals, openModal, closeModal } = useModals([
 *   'agendamento', 'cliente', 'procedimentos'
 * ]);
 * 
 * // Abrir modal
 * <button onClick={() => openModal('agendamento')}>Novo</button>
 * 
 * // Renderizar modal
 * {modals.agendamento && (
 *   <ModalAgendamento onClose={() => closeModal('agendamento')} />
 * )}
 */
export function useModals<T extends string>(modalNames: readonly T[]): UseModalsReturn<T> {
  const initialState = useMemo(() => {
    return modalNames.reduce((acc, name) => {
      acc[name] = false;
      return acc;
    }, {} as ModalState<T>);
  }, [modalNames]);

  const [modals, setModals] = useState<ModalState<T>>(initialState);

  const openModal = useCallback((name: T) => {
    setModals(prev => ({ ...prev, [name]: true }));
  }, []);

  const closeModal = useCallback((name: T) => {
    setModals(prev => ({ ...prev, [name]: false }));
  }, []);

  const toggleModal = useCallback((name: T) => {
    setModals(prev => ({ ...prev, [name]: !prev[name] }));
  }, []);

  const closeAll = useCallback(() => {
    setModals(initialState);
  }, [initialState]);

  const isOpen = useCallback((name: T) => {
    return modals[name] || false;
  }, [modals]);

  return {
    modals,
    openModal,
    closeModal,
    toggleModal,
    closeAll,
    isOpen
  };
}
