'use client';

import { useEffect, useRef, useState } from 'react';
import { getPrimaryApiBaseUrl } from '@/lib/api-base';
import { prepararArquivoImagemUpload } from '@/lib/image-prepare';
import { MAX_FOTOS_POR_CONSULTA } from '@/components/clinica-beleza/consultas/fotos/fotos-constants';

function normalizarTokenFoto(raw: string | null | undefined): string {
  const value = (raw || '').trim();
  if (!value) return '';
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export interface FotoUploadConfig {
  paciente_nome: string;
  profissional_nome?: string;
  clinica_nome: string;
  max_fotos?: number;
  fotos_consulta_count?: number;
  fotos_restantes?: number;
}

export interface ArquivoPendente {
  id: string;
  file: File;
  preview: string;
}

const EXT_IMAGEM = /\.(jpe?g|png|gif|webp|heic|heif|bmp)$/i;
const FECHAR_APOS_ENVIO_MS = 1800;

function fecharPaginaAposEnvio() {
  window.close();
  if (window.history.length > 1) {
    window.history.back();
  }
}

function arquivoEhImagem(file: File): boolean {
  if (file.type.startsWith('image/')) return true;
  return EXT_IMAGEM.test(file.name);
}

export function useEnviarFotoPublica(tokenProp: string | null | undefined) {
  const token = normalizarTokenFoto(tokenProp);
  const tokenApiSegment = token ? encodeURIComponent(token) : '';

  const [loading, setLoading] = useState(true);
  const [config, setConfig] = useState<FotoUploadConfig | null>(null);
  const [erro, setErro] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [preparando, setPreparando] = useState(false);
  const [progressoEnvio, setProgressoEnvio] = useState('');
  const [fotosEnviadas, setFotosEnviadas] = useState(0);
  const [pendentes, setPendentes] = useState<ArquivoPendente[]>([]);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const galeriaInputRef = useRef<HTMLInputElement>(null);

  const maxFotos = config?.max_fotos ?? MAX_FOTOS_POR_CONSULTA;
  const fotosRestantes =
    typeof config?.fotos_restantes === 'number'
      ? Math.max(0, config.fotos_restantes - fotosEnviadas)
      : Math.max(0, maxFotos - fotosEnviadas);
  const maxNesteEnvio = Math.max(0, fotosRestantes);

  const limparPendentes = () => {
    pendentes.forEach((p) => URL.revokeObjectURL(p.preview));
    setPendentes([]);
  };

  useEffect(() => {
    return () => {
      pendentes.forEach((p) => URL.revokeObjectURL(p.preview));
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    (async () => {
      if (!tokenApiSegment) {
        setErro('Link inválido ou incompleto.');
        setLoading(false);
        return;
      }
      try {
        const url = getPrimaryApiBaseUrl();
        const res = await fetch(`${url}/clinica-beleza/enviar-foto/${tokenApiSegment}/`);
        const data = await res.json();
        if (!res.ok) {
          setErro(data.error || 'Link inválido.');
          return;
        }
        setConfig(data);
      } catch {
        setErro('Erro ao carregar. Verifique sua conexão.');
      } finally {
        setLoading(false);
      }
    })();
  }, [tokenApiSegment]);

  const enviarArquivo = async (file: File): Promise<boolean> => {
    if (!config) return false;
    const api = getPrimaryApiBaseUrl();
    const formData = new FormData();
    formData.append('file', file);

    let res: Response;
    try {
      res = await fetch(`${api}/clinica-beleza/enviar-foto/${tokenApiSegment}/`, {
        method: 'POST',
        body: formData,
      });
    } catch {
      setErro('Sem conexão ao enviar a imagem. Verifique a internet do celular.');
      return false;
    }
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setErro(data.error || 'Erro ao registrar foto.');
      return false;
    }
    return true;
  };

  const confirmarEnvio = async () => {
    if (!pendentes.length) return;
    setEnviando(true);
    setErro('');
    let enviadas = 0;
    try {
      for (let i = 0; i < pendentes.length; i++) {
        setProgressoEnvio(`Enviando ${i + 1} de ${pendentes.length}…`);
        const ok = await enviarArquivo(pendentes[i].file);
        if (!ok) return;
        enviadas += 1;
      }
      limparPendentes();
      setFotosEnviadas(enviadas);
    } catch {
      setErro('Erro ao enviar. Tente novamente.');
    } finally {
      setEnviando(false);
      setProgressoEnvio('');
    }
  };

  const adicionarArquivos = async (files: FileList | null) => {
    if (!files?.length) return;
    const imagens = Array.from(files).filter(arquivoEhImagem);
    if (!imagens.length) {
      setErro('Selecione apenas imagens (JPG, PNG, etc.).');
      return;
    }
    const restante = maxNesteEnvio - pendentes.length;
    if (restante <= 0) {
      setErro(
        maxNesteEnvio <= 0
          ? `Máximo de ${maxFotos} fotos por consulta já atingido.`
          : `Máximo de ${maxNesteEnvio} foto(s) restantes nesta consulta.`,
      );
      return;
    }

    setPreparando(true);
    setErro('');
    try {
      const selecionadas = imagens.slice(0, restante);
      const novos: ArquivoPendente[] = [];
      for (const original of selecionadas) {
        const file = await prepararArquivoImagemUpload(original);
        novos.push({
          id: `${file.name}-${file.size}-${Date.now()}-${Math.random()}`,
          file,
          preview: URL.createObjectURL(file),
        });
      }
      if (imagens.length > restante) {
        setErro(`Só é possível adicionar mais ${restante} foto(s) nesta consulta.`);
      }
      setPendentes((prev) => [...prev, ...novos]);
    } catch {
      setErro('Não foi possível preparar a imagem. Tente outra foto.');
    } finally {
      setPreparando(false);
    }
  };

  const removerPendente = (id: string) => {
    setPendentes((prev) => {
      const item = prev.find((p) => p.id === id);
      if (item) URL.revokeObjectURL(item.preview);
      return prev.filter((p) => p.id !== id);
    });
  };

  const onCameraChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    void adicionarArquivos(e.target.files);
    e.target.value = '';
  };

  const onGaleriaChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    void adicionarArquivos(e.target.files);
    e.target.value = '';
  };

  useEffect(() => {
    if (fotosEnviadas <= 0) return;
    const timer = window.setTimeout(fecharPaginaAposEnvio, FECHAR_APOS_ENVIO_MS);
    return () => window.clearTimeout(timer);
  }, [fotosEnviadas]);

  return {
    loading,
    config,
    erro,
    enviando,
    preparando,
    progressoEnvio,
    fotosEnviadas,
    pendentes,
    cameraInputRef,
    galeriaInputRef,
    maxFotos,
    maxNesteEnvio,
    setErro,
    onCameraChange,
    onGaleriaChange,
    confirmarEnvio,
    removerPendente,
  };
}
