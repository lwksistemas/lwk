'use client';

import { useEffect, useRef, useState } from 'react';
import {
  Camera,
  CheckCircle,
  AlertCircle,
  Upload,
  Stethoscope,
  Images,
  X,
} from 'lucide-react';
import { getPrimaryApiBaseUrl } from '@/lib/api-base';
import { prepararArquivoImagemUpload } from '@/lib/cloudinary-direct-upload';
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

interface FotoUploadConfig {
  paciente_nome: string;
  profissional_nome?: string;
  clinica_nome: string;
  cloud_name: string;
  upload_preset: string;
  folder: string;
  max_fotos?: number;
  fotos_consulta_count?: number;
  fotos_restantes?: number;
}

interface ArquivoPendente {
  id: string;
  file: File;
  preview: string;
}

const EXT_IMAGEM = /\.(jpe?g|png|gif|webp|heic|heif|bmp)$/i;
const FECHAR_APOS_ENVIO_MS = 1800;

/** Fecha aba/janela após envio (QR abre link novo a cada consulta). */
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

export function EnviarFotoPublicaClient({ token: tokenProp }: { token?: string | null }) {
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
    // `file` já vem comprimido de adicionarArquivos
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <p className="text-gray-600">Carregando…</p>
      </div>
    );
  }

  if (fotosEnviadas > 0) {
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

  if (erro && !config) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-red-50 p-4">
        <div className="bg-white rounded-2xl shadow-lg p-8 max-w-sm w-full text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
          <p className="text-gray-800">{erro}</p>
        </div>
      </div>
    );
  }

  const temPendentes = pendentes.length > 0;

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50 to-white p-4 pb-8">
      <div className="max-w-md mx-auto">
        <div className="text-center pt-8 pb-6">
          <div className="inline-flex p-3 rounded-full bg-purple-100 mb-3">
            <Stethoscope className="w-8 h-8 text-purple-700" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Foto do paciente</h1>
          <p className="text-gray-600 mt-1">{config?.clinica_nome}</p>
          <p className="text-sm font-medium text-gray-800 mt-3">
            Paciente: {config?.paciente_nome}
          </p>
          {config?.profissional_nome && (
            <p className="text-xs text-gray-500 mt-1">Profissional: {config.profissional_nome}</p>
          )}
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-6 space-y-4">
          <p className="text-sm text-gray-600 text-center">
            {preparando
              ? 'Otimizando foto para envio…'
              : temPendentes
                ? 'Confira as fotos selecionadas e toque em Enviar.'
                : 'Use a câmera do celular ou o botão Galeria para escolher fotos já salvas.'}
          </p>

          {temPendentes && (
            <div className="grid grid-cols-3 gap-2">
              {pendentes.map((item) => (
                <div key={item.id} className="relative aspect-square rounded-lg overflow-hidden border border-gray-200 bg-gray-100">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={item.preview} alt="Prévia" className="w-full h-full object-cover" />
                  {!enviando && (
                    <button
                      type="button"
                      onClick={() => removerPendente(item.id)}
                      className="absolute top-1 right-1 p-1 rounded-full bg-black/60 text-white"
                      aria-label="Remover foto"
                    >
                      <X size={14} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          {temPendentes && (
            <p className="text-xs text-center text-gray-500">
              {pendentes.length} foto{pendentes.length !== 1 ? 's' : ''} selecionada
              {pendentes.length !== 1 ? 's' : ''}
              {pendentes.length < maxNesteEnvio && ' — você pode adicionar mais'}
            </p>
          )}

          {erro && (
            <p className="text-sm text-red-600 text-center flex items-center justify-center gap-1">
              <AlertCircle size={16} />
              {erro}
            </p>
          )}

          <input
            ref={cameraInputRef}
            type="file"
            accept="image/*"
            capture="user"
            className="hidden"
            onChange={onCameraChange}
          />
          <input
            ref={galeriaInputRef}
            type="file"
            accept="image/*"
            multiple
            className="hidden"
            onChange={onGaleriaChange}
          />

          {maxNesteEnvio <= 0 && !temPendentes ? (
            <p className="text-sm text-center text-amber-800 bg-amber-50 border border-amber-200 rounded-xl px-3 py-3">
              Limite de {maxFotos} fotos por consulta já atingido.
            </p>
          ) : temPendentes ? (
            <div className="space-y-3">
              <button
                type="button"
                disabled={enviando}
                onClick={() => void confirmarEnvio()}
                className="w-full flex items-center justify-center gap-2 py-4 rounded-xl bg-green-600 text-white font-semibold text-lg disabled:opacity-50"
              >
                {enviando ? (
                  <>
                    <Upload className="animate-pulse" size={22} />
                    {progressoEnvio || 'Enviando…'}
                  </>
                ) : (
                  <>
                    <CheckCircle size={22} />
                    Enviar {pendentes.length} foto{pendentes.length !== 1 ? 's' : ''}
                  </>
                )}
              </button>
              {!enviando && pendentes.length < maxNesteEnvio && (
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => cameraInputRef.current?.click()}
                    className="flex items-center justify-center gap-2 py-3 rounded-xl border border-gray-300 text-gray-700 font-medium text-sm"
                  >
                    <Camera size={18} />
                    Câmera
                  </button>
                  <button
                    type="button"
                    onClick={() => galeriaInputRef.current?.click()}
                    className="flex items-center justify-center gap-2 py-3 rounded-xl border border-gray-300 text-gray-700 font-medium text-sm"
                  >
                    <Images size={18} />
                    Galeria
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3">
              <button
                type="button"
                disabled={enviando || preparando}
                onClick={() => cameraInputRef.current?.click()}
                className="w-full flex items-center justify-center gap-2 py-4 rounded-xl bg-purple-700 text-white font-semibold text-lg disabled:opacity-50"
              >
                <Camera size={22} />
                Tirar foto (câmera)
              </button>
              <button
                type="button"
                disabled={enviando || preparando}
                onClick={() => galeriaInputRef.current?.click()}
                className="w-full flex items-center justify-center gap-2 py-4 rounded-xl border-2 border-purple-300 bg-purple-50 text-purple-900 font-semibold text-lg disabled:opacity-50"
              >
                <Images size={22} />
                Galeria — escolher fotos salvas
              </button>
              <p className="text-xs text-center text-gray-500 px-2">
                Até {maxNesteEnvio} foto(s) restantes nesta consulta (máx. {maxFotos}).
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
