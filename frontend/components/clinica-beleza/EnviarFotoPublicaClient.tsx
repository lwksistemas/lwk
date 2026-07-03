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
}

interface ArquivoPendente {
  id: string;
  file: File;
  preview: string;
}

const MAX_FOTOS = 20;
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

const LIMITE_CLOUDINARY_BYTES = 9 * 1024 * 1024;
const MAX_LADO_INICIAL = 1920;

type FonteImagem = ImageBitmap | HTMLImageElement;

async function carregarFonteImagem(file: File): Promise<FonteImagem | null> {
  if (typeof createImageBitmap === 'function') {
    try {
      return await createImageBitmap(file);
    } catch {
      /* fallback abaixo */
    }
  }
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve(img);
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('imagem inválida'));
    };
    img.src = url;
  });
}

function liberarFonteImagem(fonte: FonteImagem) {
  if ('close' in fonte && typeof fonte.close === 'function') fonte.close();
}

function dimensoesFonte(fonte: FonteImagem) {
  return { w: fonte.width, h: fonte.height };
}

async function canvasParaJpeg(
  canvas: HTMLCanvasElement,
  qualidade: number,
): Promise<Blob | null> {
  return new Promise((resolve) => {
    canvas.toBlob((b) => resolve(b), 'image/jpeg', qualidade);
  });
}

/** Reduz fotos do celular antes do upload (limite Cloudinary: 10 MB). */
async function prepararArquivoUpload(file: File): Promise<File> {
  try {
    const fonte = await carregarFonteImagem(file);
    if (!fonte) return file;

    const { w: iw, h: ih } = dimensoesFonte(fonte);
    let maxLado = MAX_LADO_INICIAL;
    let resultado: File | null = null;

    while (maxLado >= 960) {
      const escala = Math.min(1, maxLado / Math.max(iw, ih));
      const w = Math.max(1, Math.round(iw * escala));
      const h = Math.max(1, Math.round(ih * escala));
      const canvas = document.createElement('canvas');
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext('2d');
      if (!ctx) break;
      ctx.drawImage(fonte, 0, 0, w, h);

      let qualidade = 0.88;
      let blob: Blob | null = null;
      while (qualidade >= 0.45) {
        blob = await canvasParaJpeg(canvas, qualidade);
        if (blob && blob.size <= LIMITE_CLOUDINARY_BYTES) break;
        qualidade -= 0.08;
      }
      if (blob && blob.size <= LIMITE_CLOUDINARY_BYTES) {
        const nome = file.name.replace(EXT_IMAGEM, '.jpg') || 'foto.jpg';
        resultado = new File([blob], nome, { type: 'image/jpeg' });
        break;
      }
      maxLado = Math.round(maxLado * 0.75);
    }

    liberarFonteImagem(fonte);
    return resultado ?? file;
  } catch {
    return file;
  }
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
    const arquivo = await prepararArquivoUpload(file);
    const api = getPrimaryApiBaseUrl();
    const formData = new FormData();
    formData.append('file', arquivo);

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
    const restante = MAX_FOTOS - pendentes.length;
    if (restante <= 0) {
      setErro(`Máximo de ${MAX_FOTOS} fotos por envio.`);
      return;
    }

    setPreparando(true);
    setErro('');
    try {
      const selecionadas = imagens.slice(0, restante);
      const novos: ArquivoPendente[] = [];
      for (const original of selecionadas) {
        const file = await prepararArquivoUpload(original);
        novos.push({
          id: `${file.name}-${file.size}-${Date.now()}-${Math.random()}`,
          file,
          preview: URL.createObjectURL(file),
        });
      }
      if (imagens.length > restante) {
        setErro(`Só é possível adicionar mais ${restante} foto(s) neste envio.`);
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
              {pendentes.length < MAX_FOTOS && ' — você pode adicionar mais'}
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

          {temPendentes ? (
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
              {!enviando && pendentes.length < MAX_FOTOS && (
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
                Na galeria você pode marcar várias fotos de uma vez antes de confirmar o envio.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
