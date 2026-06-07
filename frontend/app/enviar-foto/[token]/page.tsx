'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams } from 'next/navigation';
import { Camera, CheckCircle, AlertCircle, Upload } from 'lucide-react';
import { getPrimaryApiBaseUrl } from '@/lib/api-base';

interface FotoUploadConfig {
  paciente_nome: string;
  clinica_nome: string;
  cloud_name: string;
  upload_preset: string;
  folder: string;
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
  const [sucesso, setSucesso] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

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

  const enviarArquivo = async (file: File) => {
    if (!config) return;
    setEnviando(true);
    setErro('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('upload_preset', config.upload_preset);
      formData.append('folder', config.folder);

      const up = await fetch(
        `https://api.cloudinary.com/v1_1/${config.cloud_name}/image/upload`,
        { method: 'POST', body: formData },
      );
      const upData = await up.json();
      if (!up.ok || !upData.secure_url) {
        setErro(upData.error?.message || 'Falha no envio da imagem.');
        return;
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
        return;
      }
      setSucesso(true);
    } catch {
      setErro('Erro ao enviar. Tente novamente.');
    } finally {
      setEnviando(false);
    }
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setErro('Selecione uma imagem.');
      return;
    }
    setPreview(URL.createObjectURL(file));
    void enviarArquivo(file);
    e.target.value = '';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <p className="text-gray-600">Carregando…</p>
      </div>
    );
  }

  if (sucesso) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-green-50 p-4">
        <div className="bg-white rounded-2xl shadow-lg p-8 max-w-sm w-full text-center">
          <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
          <h1 className="text-xl font-bold text-gray-900 mb-2">Foto enviada!</h1>
          <p className="text-gray-600 text-sm">
            A clínica já pode ver a foto no acompanhamento da consulta.
          </p>
          <button
            type="button"
            onClick={() => {
              setSucesso(false);
              setPreview(null);
            }}
            className="mt-6 w-full py-3 rounded-lg bg-green-600 text-white font-medium"
          >
            Enviar outra foto
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

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50 to-white p-4 pb-8">
      <div className="max-w-md mx-auto">
        <div className="text-center pt-8 pb-6">
          <div className="inline-flex p-3 rounded-full bg-purple-100 mb-3">
            <Camera className="w-8 h-8 text-purple-700" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Enviar foto</h1>
          <p className="text-gray-600 mt-1">{config?.clinica_nome}</p>
          <p className="text-sm text-gray-500 mt-2">Paciente: {config?.paciente_nome}</p>
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-6 space-y-4">
          <p className="text-sm text-gray-600 text-center">
            Tire ou escolha uma foto do paciente para o acompanhamento do tratamento.
          </p>

          {preview && (
            <div className="rounded-xl overflow-hidden border border-gray-200">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={preview} alt="Prévia" className="w-full max-h-64 object-contain bg-gray-100" />
            </div>
          )}

          {erro && (
            <p className="text-sm text-red-600 text-center flex items-center justify-center gap-1">
              <AlertCircle size={16} />
              {erro}
            </p>
          )}

          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={onFileChange}
          />

          <button
            type="button"
            disabled={enviando}
            onClick={() => inputRef.current?.click()}
            className="w-full flex items-center justify-center gap-2 py-4 rounded-xl bg-purple-700 text-white font-semibold text-lg disabled:opacity-50"
          >
            {enviando ? (
              <>
                <Upload className="animate-pulse" size={22} />
                Enviando…
              </>
            ) : (
              <>
                <Camera size={22} />
                Tirar / escolher foto
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
