'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams } from 'next/navigation';
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

function arquivoEhImagem(file: File): boolean {
  if (file.type.startsWith('image/')) return true;
  return EXT_IMAGEM.test(file.name);
}

/** Reduz fotos grandes do celular antes do upload (evita falha no Cloudinary). */
async function prepararArquivoUpload(file: File): Promise<File> {
  const LIMITE_MB = 8;
  const MAX_LADO = 2400;
  if (file.size <= LIMITE_MB * 1024 * 1024) return file;
  if (typeof createImageBitmap !== 'function') return file;

  try {
    const bitmap = await createImageBitmap(file);
    const escala = Math.min(1, MAX_LADO / Math.max(bitmap.width, bitmap.height));
    const w = Math.max(1, Math.round(bitmap.width * escala));
    const h = Math.max(1, Math.round(bitmap.height * escala));
    const canvas = document.createElement('canvas');
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    if (!ctx) return file;
    ctx.drawImage(bitmap, 0, 0, w, h);
    bitmap.close();

    const blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob((b) => resolve(b), 'image/jpeg', 0.88);
    });
    if (!blob) return file;
    const nome = file.name.replace(EXT_IMAGEM, '.jpg') || 'foto.jpg';
    return new File([blob], nome, { type: 'image/jpeg' });
  } catch {
    return file;
  }
}

export default function EnviarFotoPage() {
  const params = useParams();
  const tokenRaw = params.token as string;
  let token: string;
  try {
    token = decodeURIComponent(tokenRaw);
  } catch {
    token = tokenRaw;
  }
  const tokenApiSegment = encodeURIComponent(token);

  const [loading, setLoading] = useState(true);
  const [config, setConfig] = useState<FotoUploadConfig | null>(null);
  const [erro, setErro] = useState('');
  const [enviando, setEnviando] = useState(false);
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
    const formData = new FormData();
    formData.append('file', arquivo);
    formData.append('upload_preset', config.upload_preset);
    formData.append('folder', config.folder);

    let up: Response;
    try {
      up = await fetch(
        `https://api.cloudinary.com/v1_1/${config.cloud_name}/image/upload`,
        { method: 'POST', body: formData },
      );
    } catch {
      setErro('Sem conexão ao enviar a imagem. Verifique a internet do celular.');
      return false;
    }
    const upData = await up.json().catch(() => ({}));
    if (!up.ok || !upData.secure_url) {
      const detalhe = upData.error?.message || upData.error || '';
      setErro(detalhe ? `Falha no upload: ${detalhe}` : 'Falha no envio da imagem. Tente outra foto ou use a câmera.');
      return false;
    }

    const api = getPrimaryApiBaseUrl();
    const res = await fetch(`${api}/clinica-beleza/enviar-foto/${tokenApiSegment}/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cloudinary_url: upData.secure_url,
        cloudinary_public_id: upData.public_id || '',
      }),
    });
    const data = await res.json();
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

  const adicionarArquivos = (files: FileList | null) => {
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
    const novos = imagens.slice(0, restante).map((file) => ({
      id: `${file.name}-${file.size}-${Date.now()}-${Math.random()}`,
      file,
      preview: URL.createObjectURL(file),
    }));
    if (imagens.length > restante) {
      setErro(`Só é possível adicionar mais ${restante} foto(s) neste envio.`);
    } else {
      setErro('');
    }
    setPendentes((prev) => [...prev, ...novos]);
  };

  const removerPendente = (id: string) => {
    setPendentes((prev) => {
      const item = prev.find((p) => p.id === id);
      if (item) URL.revokeObjectURL(item.preview);
      return prev.filter((p) => p.id !== id);
    });
  };

  const onCameraChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    adicionarArquivos(e.target.files);
    e.target.value = '';
  };

  const onGaleriaChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    adicionarArquivos(e.target.files);
    e.target.value = '';
  };

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
            {fotosEnviadas === 1
              ? 'A foto já aparece na aba Fotos da consulta no computador.'
              : 'As fotos já aparecem na aba Fotos da consulta no computador.'}
          </p>
          <button
            type="button"
            onClick={() => setFotosEnviadas(0)}
            className="mt-6 w-full py-3 rounded-lg bg-green-600 text-white font-medium"
          >
            Enviar mais fotos
          </button>
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
            {temPendentes
              ? 'Confira as fotos selecionadas antes de enviar.'
              : (
                <>
                  Fotografe o paciente ou escolha <strong>várias fotos</strong> da galeria do seu
                  celular.
                </>
              )}
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
            capture="environment"
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
                disabled={enviando}
                onClick={() => cameraInputRef.current?.click()}
                className="w-full flex items-center justify-center gap-2 py-4 rounded-xl bg-purple-700 text-white font-semibold text-lg disabled:opacity-50"
              >
                <Camera size={22} />
                Fotografar paciente
              </button>
              <button
                type="button"
                disabled={enviando}
                onClick={() => galeriaInputRef.current?.click()}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl border-2 border-purple-200 text-purple-800 font-semibold disabled:opacity-50"
              >
                <Images size={22} />
                Escolher da galeria
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
