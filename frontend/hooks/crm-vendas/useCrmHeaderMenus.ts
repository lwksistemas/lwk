'use client';

import { useEffect, useRef, useState } from 'react';
import apiClient from '@/lib/api-client';

export function useCrmHeaderMenus(slug: string) {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNovoMenu, setShowNovoMenu] = useState(false);
  const [showSuporteMenu, setShowSuporteMenu] = useState(false);
  const [modalSuporteAberto, setModalSuporteAberto] = useState(false);
  const [lojaNome, setLojaNome] = useState('');

  const novoRef = useRef<HTMLDivElement>(null);
  const suporteRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (novoRef.current && !novoRef.current.contains(e.target as Node)) {
        setShowNovoMenu(false);
      }
      if (suporteRef.current && !suporteRef.current.contains(e.target as Node)) {
        setShowSuporteMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (!slug) return;
    apiClient
      .get(`/superadmin/lojas/info_publica/?slug=${slug}`)
      .then((res) => setLojaNome(res.data?.nome || ''))
      .catch(() => setLojaNome(''));
  }, [slug]);

  return {
    showUserMenu,
    setShowUserMenu,
    showNovoMenu,
    setShowNovoMenu,
    showSuporteMenu,
    setShowSuporteMenu,
    modalSuporteAberto,
    setModalSuporteAberto,
    lojaNome,
    novoRef,
    suporteRef,
    searchRef,
  };
}
