'use client';

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  // ⚠️ IMPORTANTE:
  // A partir de agora queremos que o tema padrão do sistema seja SEMPRE "claro"
  // nas lojas, independentemente do tema do sistema operacional.
  // Por isso o estado inicial é "light" e só mudamos se o usuário escolher.
  const [theme, setThemeState] = useState<Theme>('light');
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light');
  const [mounted, setMounted] = useState(false);

  // Detectar preferência do sistema
  const getSystemTheme = useCallback((): 'light' | 'dark' => {
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return 'light';
  }, []);

  // Resolver tema atual
  const resolveTheme = useCallback((currentTheme: Theme): 'light' | 'dark' => {
    if (currentTheme === 'system') {
      return getSystemTheme();
    }
    return currentTheme;
  }, [getSystemTheme]);

  // Aplicar tema no documento
  const applyTheme = useCallback((resolved: 'light' | 'dark') => {
    if (typeof document !== 'undefined') {
      const root = document.documentElement;
      root.classList.remove('light', 'dark');
      root.classList.add(resolved);
    }
  }, []);

  // Inicialização
  useEffect(() => {
    setMounted(true);
    
    try {
      // Carregar tema salvo (se existir). Caso contrário, usar "light" como padrão.
      const savedTheme = (typeof window !== 'undefined' && window.localStorage) 
        ? localStorage.getItem('theme') as Theme | null 
        : null;
      const initialTheme = savedTheme || 'light';
      setThemeState(initialTheme);
      
      const resolved = resolveTheme(initialTheme);
      setResolvedTheme(resolved);
      applyTheme(resolved);
    } catch (error) {
      // Fallback se localStorage não estiver disponível
      console.warn('localStorage not available, using default theme');
      setThemeState('light');
      setResolvedTheme('light');
      applyTheme('light');
    }
  }, [resolveTheme, applyTheme]);

  // Listener para mudanças de preferência do sistema
  useEffect(() => {
    if (theme !== 'system' || typeof window === 'undefined') return;

    try {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      
      const handleChange = () => {
        const resolved = resolveTheme('system');
        setResolvedTheme(resolved);
        applyTheme(resolved);
      };

      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    } catch (error) {
      console.warn('matchMedia not available');
    }
  }, [theme, resolveTheme, applyTheme]);

  // Função para definir tema
  const setTheme = useCallback((newTheme: Theme) => {
    setThemeState(newTheme);
    
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        localStorage.setItem('theme', newTheme);
      }
    } catch (error) {
      console.warn('localStorage not available');
    }
    
    const resolved = resolveTheme(newTheme);
    setResolvedTheme(resolved);
    applyTheme(resolved);
  }, [resolveTheme, applyTheme]);

  // Toggle entre light e dark
  const toggleTheme = useCallback(() => {
    const newTheme = resolvedTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
  }, [resolvedTheme, setTheme]);

  // Evitar flash de tema errado no SSR
  if (!mounted) {
    return <>{children}</>;
  }

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

// Componente de botão para alternar tema
export function ThemeToggle({ className = '' }: { className?: string }) {
  const { resolvedTheme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={`
        p-2 rounded-lg transition-all duration-200
        bg-gray-100 dark:bg-gray-700
        hover:bg-gray-200 dark:hover:bg-gray-600
        text-gray-600 dark:text-gray-300
        ${className}
      `}
      title={resolvedTheme === 'light' ? 'Ativar modo escuro' : 'Ativar modo claro'}
    >
      {resolvedTheme === 'light' ? (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
      ) : (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      )}
    </button>
  );
}
