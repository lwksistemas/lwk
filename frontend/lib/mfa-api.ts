import apiClient from '@/lib/api-client';

export interface MfaStatus {
  mfa_available: boolean;
  mfa_enabled: boolean;
}

export interface MfaSetupResponse {
  secret: string;
  provisioning_uri: string;
  qr_code_base64: string;
  message: string;
}

export async function fetchMfaStatus(): Promise<MfaStatus> {
  const { data } = await apiClient.get<MfaStatus>('/auth/mfa/status/');
  return data;
}

export async function setupMfa(): Promise<MfaSetupResponse> {
  const { data } = await apiClient.post<MfaSetupResponse>('/auth/mfa/setup/');
  return data;
}

export async function confirmMfa(otpCode: string): Promise<void> {
  await apiClient.post('/auth/mfa/confirm/', { otp_code: otpCode });
}

export async function disableMfa(otpCode: string): Promise<void> {
  await apiClient.post('/auth/mfa/disable/', { otp_code: otpCode });
}
