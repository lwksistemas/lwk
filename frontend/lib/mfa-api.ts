import apiClient from '@/lib/api-client';

export interface MfaStatus {
  mfa_available: boolean;
  mfa_enabled: boolean;
  backup_codes_remaining?: number;
}

export interface MfaSetupResponse {
  secret: string;
  provisioning_uri: string;
  qr_code_base64: string;
  message: string;
}

export interface MfaConfirmResponse {
  message: string;
  mfa_enabled: boolean;
  backup_codes?: string[];
  backup_codes_hint?: string;
}

export async function fetchMfaStatus(): Promise<MfaStatus> {
  const { data } = await apiClient.get<MfaStatus>('/auth/mfa/status/');
  return data;
}

export async function setupMfa(): Promise<MfaSetupResponse> {
  const { data } = await apiClient.post<MfaSetupResponse>('/auth/mfa/setup/');
  return data;
}

export async function confirmMfa(otpCode: string): Promise<MfaConfirmResponse> {
  const { data } = await apiClient.post<MfaConfirmResponse>('/auth/mfa/confirm/', {
    otp_code: otpCode,
  });
  return data;
}

export async function disableMfa(otpCode: string): Promise<void> {
  await apiClient.post('/auth/mfa/disable/', { otp_code: otpCode });
}

export async function regenerateMfaBackupCodes(otpCode: string): Promise<{ backup_codes: string[] }> {
  const { data } = await apiClient.post<{ backup_codes: string[] }>(
    '/auth/mfa/regenerate-backup/',
    { otp_code: otpCode },
  );
  return data;
}
