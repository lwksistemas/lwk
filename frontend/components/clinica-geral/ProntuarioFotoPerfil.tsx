'use client';

import { useRef, useState } from 'react';
import { Camera, ImagePlus, Loader2, User, X } from 'lucide-react';
import { ImageUploadMedia } from '@/components/ImageUploadMedia';
import {
  capturarFotoDoVideo,
  isArquivoImagemValido,
  mensagemErroCamera,
  obterStreamCamera,
} from '@/components/clinica-beleza/paciente-foto-cadastro/paciente-foto-cadastro-utils';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { Paciente } from '@/lib/clinica-geral-types';

type ProntuarioFotoPerfilProps = {
  paciente: Paciente;
  onChange: (url: string) => Promise<void>;
};

export function ProntuarioFotoPerfil({ paciente, onChange }: ProntuarioFotoPerfilProps) {
  const [aberto, setAberto] = useState(false);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [erro, setErro] = useState('');
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const fecharCamera = () => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setCameraOpen(false);
  };

  const fechar = () => {
    fecharCamera();
    setAberto(false);
    setErro('');
  };

  const salvar = async (url: string) => {
    setUploading(true);
    setErro('');
    try {
      await onChange(url);
      fechar();
    } catch {
      setErro('Não foi possível salvar a foto.');
    } finally {
      setUploading(false);
    }
  };

  const abrirCamera = async () => {
    setErro('');
    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
      setErro('Seu navegador não suporta captura pela câmera.');
      return;
    }
    if (!window.isSecureContext) {
      setErro('A câmera só funciona em conexão segura (HTTPS).');
      return;
    }
    try {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = await obterStreamCamera();
      setCameraOpen(true);
      requestAnimationFrame(() => {
        const video = videoRef.current;
        if (video && streamRef.current) {
          video.srcObject = streamRef.current;
          void video.play();
        }
      });
    } catch (err) {
      setErro(mensagemErroCamera(err));
    }
  };

  const capturar = async () => {
    const video = videoRef.current;
    if (!video?.videoWidth) {
      setErro('Aguarde a câmera carregar e tente novamente.');
      return;
    }
    const blob = await capturarFotoDoVideo(video);
    fecharCamera();
    if (!blob) {
      setErro('Erro ao capturar a foto.');
      return;
    }
    const file = new File([blob], 'foto-paciente.jpg', { type: 'image/jpeg' });
    if (!isArquivoImagemValido(file)) {
      setErro('Selecione um arquivo de imagem.');
      return;
    }
    setUploading(true);
    try {
      const { default: apiClient } = await import('@/lib/api-client');
      const formData = new FormData();
      formData.append('file', file);
      formData.append('folder', 'fotos');
      formData.append('patient_id', String(paciente.id));
      if (paciente.nome) formData.append('patient_nome', paciente.nome);
      if (paciente.cpf) formData.append('patient_cpf', paciente.cpf);
      const res = await apiClient.post<{ url: string }>('/media/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      if (!res.data?.url) throw new Error('upload');
      await onChange(res.data.url);
      fechar();
    } catch {
      setErro('Não foi possível enviar a foto.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setAberto(true)}
        className="relative flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-full bg-slate-200 text-slate-400 hover:ring-2 hover:ring-teal-500"
        title="Importar ou tirar foto"
        aria-label="Alterar foto do paciente"
      >
        {paciente.foto_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={paciente.foto_url} alt="" className="h-full w-full object-cover" />
        ) : (
          <User className="h-8 w-8" />
        )}
      </button>

      {aberto ? (
        <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/45 p-4" onClick={fechar}>
          <div
            className="w-full max-w-sm rounded-xl bg-white p-5 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-800">Foto do paciente</h3>
              <button type="button" onClick={fechar} aria-label="Fechar" className="text-slate-400 hover:text-slate-600">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="mx-auto mb-4 flex h-28 w-28 items-center justify-center overflow-hidden rounded-full bg-slate-100 text-slate-400">
              {paciente.foto_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={paciente.foto_url} alt="" className="h-full w-full object-cover" />
              ) : (
                <User className="h-12 w-12" />
              )}
            </div>
            {cameraOpen ? (
              <div className="space-y-3">
                <video ref={videoRef} autoPlay playsInline muted className="w-full rounded-lg bg-black" style={{ transform: 'scaleX(-1)' }} />
                <div className="flex gap-2">
                  <button type="button" onClick={fecharCamera} className="flex-1 rounded-md border border-slate-300 py-2 text-sm">
                    Cancelar
                  </button>
                  <button
                    type="button"
                    disabled={uploading}
                    onClick={() => void capturar()}
                    className="flex-1 rounded-md py-2 text-sm font-medium text-white disabled:opacity-60"
                    style={{ backgroundColor: TEAL }}
                  >
                    {uploading ? 'Enviando...' : 'Capturar'}
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <ImagePlus className="h-4 w-4" style={{ color: TEAL }} />
                  <ImageUploadMedia
                    compact
                    folder="fotos"
                    accept="image/*"
                    buttonLabel={uploading ? 'Enviando...' : 'Importar foto'}
                    disabled={uploading}
                    patientId={paciente.id}
                    patientNome={paciente.nome}
                    patientCpf={paciente.cpf}
                    onChange={(url) => {
                      if (url) void salvar(url);
                    }}
                  />
                </div>
                <button
                  type="button"
                  disabled={uploading}
                  onClick={() => void abrirCamera()}
                  className="flex w-full items-center justify-center gap-2 rounded-md border py-2 text-sm font-medium disabled:opacity-60"
                  style={{ borderColor: TEAL, color: TEAL }}
                >
                  {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Camera className="h-4 w-4" />}
                  Tirar foto
                </button>
                {paciente.foto_url ? (
                  <button type="button" disabled={uploading} onClick={() => void salvar('')} className="w-full py-1 text-xs text-red-500">
                    Remover foto
                  </button>
                ) : null}
              </div>
            )}
            {erro ? <p className="mt-3 text-xs text-red-600">{erro}</p> : null}
          </div>
        </div>
      ) : null}
    </>
  );
}
