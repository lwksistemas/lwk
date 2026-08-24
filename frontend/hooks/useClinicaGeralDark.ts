'use client';

import { useEffect, useState } from 'react';
import {
  applyClinicaGeralDark,
  isClinicaGeralDarkEnabled,
  persistClinicaGeralDark,
} from '@/lib/clinica-geral-theme';

/**
 * Tema claro/escuro do consultório (independente do CRM/estética).
 * Padrão: claro. `active=false` não aplica (ex.: login de outro tipo de loja).
 */
export function useClinicaGeralDark(active = true): [boolean, (value: boolean) => void] {
  const [darkMode, setDarkModeState] = useState(false);

  useEffect(() => {
    if (!active) return;
    const stored = isClinicaGeralDarkEnabled();
    setDarkModeState(stored);
    applyClinicaGeralDark(stored);
  }, [active]);

  const setDarkMode = (value: boolean) => {
    setDarkModeState(value);
    persistClinicaGeralDark(value);
  };

  return [darkMode, setDarkMode];
}
