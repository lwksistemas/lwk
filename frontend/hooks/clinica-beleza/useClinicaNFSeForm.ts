"use client";

import { useEffect, useState } from "react";
import { useClinicaNFSeConfig } from "@/contexts/ClinicaBelezaNFSeConfigContext";
import {
  nfseFormDataFromConfig,
  NFSE_FORM_DEFAULTS,
  type NFSeBannerMessage,
  type NFSeFormData,
  type NFSeTestMessage,
} from "@/components/clinica-beleza/nfse/nfse-form-types";
import apiClient from "@/lib/api-client";
import { logger } from "@/lib/logger";

export function useClinicaNFSeForm() {
  const { config, recarregar } = useClinicaNFSeConfig();

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<NFSeBannerMessage | null>(null);
  const [formData, setFormData] = useState<NFSeFormData>(NFSE_FORM_DEFAULTS);
  const [certificadoFile, setCertificadoFile] = useState<File | null>(null);
  const [issnetTestLoading, setIssnetTestLoading] = useState(false);
  const [asaasApiKey, setAsaasApiKey] = useState("");
  const [asaasWebhookToken, setAsaasWebhookToken] = useState("");
  const [asaasSandbox, setAsaasSandbox] = useState(false);
  const [issnetTestMessage, setIssnetTestMessage] = useState<NFSeTestMessage | null>(null);

  useEffect(() => {
    if (config) {
      setFormData(nfseFormDataFromConfig(config));
      setAsaasSandbox(config.asaas_sandbox ?? false);
    }
  }, [config]);

  const updateFormField = <K extends keyof NFSeFormData>(key: K, value: NFSeFormData[K]) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      const data = new FormData();
      const clearableFields = ["codigo_cnae", "codigo_nbs", "item_lista_servico", "inscricao_municipal"];
      Object.entries(formData).forEach(([key, value]) => {
        if (value === null || value === undefined) return;
        if (value === "" && !clearableFields.includes(key)) return;
        if (typeof value === "boolean") {
          data.append(key, value ? "true" : "false");
          return;
        }
        data.append(key, String(value));
      });
      if (certificadoFile) {
        data.append("issnet_certificado", certificadoFile);
      }
      if (asaasApiKey.trim()) {
        data.append("asaas_api_key", asaasApiKey.trim());
      }
      if (asaasWebhookToken.trim()) {
        data.append("asaas_webhook_token", asaasWebhookToken.trim());
      }
      data.append("asaas_sandbox", asaasSandbox ? "true" : "false");

      await apiClient.patch("/clinica-beleza/nfse-config/", data, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setMessage({ type: "success", text: "Configurações salvas com sucesso!" });
      await recarregar();
      setFormData((prev) => ({ ...prev, issnet_senha: "", issnet_senha_certificado: "" }));
      setCertificadoFile(null);
      setAsaasApiKey("");
      setAsaasWebhookToken("");
    } catch (error: unknown) {
      logger.warn("Erro ao salvar config NFS-e clínica:", error);
      const detail =
        error && typeof error === "object" && "response" in error
          ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      setMessage({
        type: "error",
        text: detail || "Erro ao salvar configurações",
      });
    } finally {
      setLoading(false);
    }
  };

  const testarConexaoIssnet = async () => {
    setIssnetTestLoading(true);
    setIssnetTestMessage(null);
    try {
      const fd = new FormData();
      fd.append("homologacao", formData.issnet_ambiente_homologacao ? "true" : "false");
      fd.append("issnet_usuario", formData.issnet_usuario.trim());
      if (formData.issnet_senha) fd.append("issnet_senha", formData.issnet_senha);
      if (formData.issnet_senha_certificado) {
        fd.append("issnet_senha_certificado", formData.issnet_senha_certificado);
      }
      if (certificadoFile) fd.append("issnet_certificado", certificadoFile);

      const res = await apiClient.post<{
        success?: boolean;
        message?: string;
        detail?: string;
      }>("/clinica-beleza/nfse-config/test-issnet/", fd);

      if (res.data?.success) {
        setIssnetTestMessage({ type: "ok", text: res.data.message || "Conexão ISSNet OK." });
      } else {
        setIssnetTestMessage({
          type: "error",
          text: res.data?.detail || "Não foi possível validar.",
        });
      }
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string; message?: string } } };
      const detail =
        ax.response?.data?.detail ||
        ax.response?.data?.message ||
        (err instanceof Error ? err.message : "Erro ao testar conexão.");
      setIssnetTestMessage({ type: "error", text: String(detail) });
    } finally {
      setIssnetTestLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.endsWith(".pfx")) {
        setMessage({ type: "error", text: "Selecione um arquivo .pfx (certificado digital A1)" });
        return;
      }
      setCertificadoFile(file);
      setMessage(null);
    }
  };

  const issnetTestDisabled =
    issnetTestLoading ||
    !formData.issnet_usuario.trim() ||
    (!certificadoFile && !config?.issnet_certificado) ||
    (!formData.issnet_senha && !formData.issnet_senha_certificado && !config?.issnet_senhas_salvas);

  return {
    config,
    loading,
    message,
    formData,
    setFormData,
    updateFormField,
    certificadoFile,
    issnetTestLoading,
    issnetTestMessage,
    asaasApiKey,
    setAsaasApiKey,
    asaasWebhookToken,
    setAsaasWebhookToken,
    asaasSandbox,
    setAsaasSandbox,
    handleSubmit,
    testarConexaoIssnet,
    handleFileChange,
    issnetTestDisabled,
  };
}

