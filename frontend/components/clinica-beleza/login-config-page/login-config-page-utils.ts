import type { LoginConfigData, LoginConfigFormState } from "./login-config-page-types";

export function normalizeHexColor(value: string): string {
  return value.startsWith("#") ? value : `#${value}`;
}

export function loginConfigDataToForm(
  data: LoginConfigData,
  defaultPrimary: string,
  defaultSecondary: string,
): LoginConfigFormState {
  return {
    logo: (data.logo ?? "").toString(),
    loginBackground: (data.login_background ?? "").toString(),
    loginLogo: (data.login_logo ?? "").toString(),
    corPrimaria: (data.cor_primaria ?? defaultPrimary).toString(),
    corSecundaria: (data.cor_secundaria ?? defaultSecondary).toString(),
  };
}

export function buildLoginConfigSaveBody(form: LoginConfigFormState): Record<string, string> {
  return {
    logo: form.logo.trim(),
    login_background: form.loginBackground.trim(),
    login_logo: form.loginLogo.trim(),
    cor_primaria: normalizeHexColor(form.corPrimaria),
    cor_secundaria: normalizeHexColor(form.corSecundaria),
  };
}

export function extractLoginConfigSaveError(e: unknown): string {
  const err = e as { response?: { data?: { error?: string; detail?: string } } };
  return (
    err?.response?.data?.error ||
    (typeof err?.response?.data?.detail === "string" ? err.response.data.detail : null) ||
    "Erro ao salvar. Tente novamente."
  );
}

export function isColorPresetSelected(
  corPrimariaHex: string,
  presetPrimaria: string,
): boolean {
  return corPrimariaHex === presetPrimaria;
}
