import apiClient from '@/lib/api-client';
import type { Notification } from '@/types/notification';

export async function fetchNotifications(): Promise<Notification[]> {
  const { data } = await apiClient.get<Notification[]>('notificacoes/');
  return Array.isArray(data) ? data : [];
}

export async function markNotificationAsRead(id: number): Promise<void> {
  await apiClient.post(`notificacoes/${id}/read/`);
}
