import { useCallback, useEffect, useRef, useState } from "react";
import {
  cloudinaryLojaClinicaPacientePerfil,
  useLojaCloudinaryDocument,
} from "@/lib/cloudinary-folders";
import { uploadImagemCloudinary } from "@/lib/cloudinary-direct-upload";
import {
  capturarFotoDoVideo,
  isArquivoImagemValido,
  mensagemErroCamera,
  obterStreamCamera,
} from "./paciente-foto-cadastro-utils";

interface UsePacienteFotoCadastroParams {
  slug: string;
  value: string;
  onChange: (url: string) => void;
  disabled?: boolean;
}

export function usePacienteFotoCadastro({ slug, value, onChange, disabled = false }: UsePacienteFotoCadastroParams) {
  const { documento: lojaDoc, ready: lojaDocReady, loading: lojaDocLoading } = useLojaCloudinaryDocument(slug);
  const folder = lojaDoc ? cloudinaryLojaClinicaPacientePerfil(lojaDoc) : "";
  const uploadDisabled = disabled || lojaDocLoading || !lojaDocReady || !folder;

  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [uploading, setUploading] = useState(false);
  const [erro, setErro] = useState("");
  const [cameraOpen, setCameraOpen] = useState(false);

  const pararCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setCameraOpen(false);
  }, []);

  useEffect(() => {
    return () => {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!cameraOpen) return;
    const video = videoRef.current;
    const stream = streamRef.current;
    if (!video || !stream) return;
    video.srcObject = stream;
    video.play().catch(() => setErro("Não foi possível iniciar a visualização da câmera."));
  }, [cameraOpen]);

  const enviarArquivo = useCallback(
    async (file: File | undefined) => {
      if (!file || !folder) return;
      if (!isArquivoImagemValido(file)) {
        setErro("Selecione um arquivo de imagem.");
        return;
      }
      setUploading(true);
      setErro("");
      try {
        const url = await uploadImagemCloudinary(file, folder);
        onChange(url);
      } catch (e: unknown) {
        setErro(e instanceof Error ? e.message : "Erro ao enviar foto.");
      } finally {
        setUploading(false);
      }
    },
    [folder, onChange],
  );

  const abrirCamera = useCallback(async () => {
    if (uploadDisabled || uploading) return;
    setErro("");
    if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      setErro("Seu navegador não suporta captura pela câmera.");
      return;
    }
    if (!window.isSecureContext) {
      setErro("A câmera só funciona em conexão segura (HTTPS).");
      return;
    }
    try {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      streamRef.current = await obterStreamCamera();
      setCameraOpen(true);
    } catch (err) {
      setErro(mensagemErroCamera(err));
    }
  }, [uploadDisabled, uploading]);

  const capturarFoto = useCallback(async () => {
    const video = videoRef.current;
    if (!video || !video.videoWidth) {
      setErro("Aguarde a câmera carregar e tente novamente.");
      return;
    }
    pararCamera();
    const blob = await capturarFotoDoVideo(video);
    if (!blob) {
      setErro("Erro ao capturar a foto.");
      return;
    }
    await enviarArquivo(new File([blob], "foto-cliente.jpg", { type: "image/jpeg" }));
  }, [enviarArquivo, pararCamera]);

  return {
    folder,
    uploadDisabled,
    lojaDocLoading,
    lojaDocReady,
    uploading,
    erro,
    cameraOpen,
    videoRef,
    pararCamera,
    abrirCamera,
    capturarFoto,
    enviarArquivo,
  };
}
