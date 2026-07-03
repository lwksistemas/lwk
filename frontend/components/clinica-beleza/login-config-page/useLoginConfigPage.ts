import { useCallback, useEffect, useState } from "react";
import apiClient from "@/lib/api-client";
import { logger } from "@/lib/logger";
import type { LoginConfigData, LoginConfigFormState } from "./login-config-page-types";
import {
  buildLoginConfigSaveBody,
  extractLoginConfigSaveError,
  loginConfigDataToForm,
} from "./login-config-page-utils";

export function useLoginConfigPage(
  apiPath: string,
  defaultPrimary: string,
  defaultSecondary: string,
) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<LoginConfigFormState>({
    logo: "",
    loginBackground: "",
    loginLogo: "",
    corPrimaria: defaultPrimary,
    corSecundaria: defaultSecondary,
  });

  const loadConfig = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get<LoginConfigData>(apiPath);
      setForm(loginConfigDataToForm(data, defaultPrimary, defaultSecondary));
    } catch (err) {
      logger.warn("Erro ao carregar config login:", err);
    } finally {
      setLoading(false);
    }
  }, [apiPath, defaultPrimary, defaultSecondary]);

  useEffect(() => {
    void loadConfig();
  }, [loadConfig]);

  const saveConfig = useCallback(async () => {
    setSaving(true);
    try {
      await apiClient.patch(apiPath, buildLoginConfigSaveBody(form));
      await loadConfig();
      alert("Configurações da tela de login salvas com sucesso!");
    } catch (e) {
      alert(extractLoginConfigSaveError(e));
    } finally {
      setSaving(false);
    }
  }, [apiPath, form, loadConfig]);

  const updateForm = useCallback((patch: Partial<LoginConfigFormState>) => {
    setForm((prev) => ({ ...prev, ...patch }));
  }, []);

  const applyColorPreset = useCallback((primaria: string, secundaria: string) => {
    setForm((prev) => ({ ...prev, corPrimaria: primaria, corSecundaria: secundaria }));
  }, []);

  return {
    loading,
    saving,
    form,
    updateForm,
    applyColorPreset,
    saveConfig,
  };
}
