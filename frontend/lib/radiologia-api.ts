import apiClient from '@/lib/api-client';
import type { Laudo, PedidoExame } from '@/lib/radiologia-types';

function unwrapList<T>(data: T[] | { results?: T[] }): T[] {
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function listPacientes(busca = '') {
  const q = busca ? `?busca=${encodeURIComponent(busca)}` : '';
  const res = await apiClient.get(`/radiologia/pacientes/${q}`);
  return unwrapList(res.data);
}

export async function listEquipamentos() {
  const res = await apiClient.get('/radiologia/equipamentos/');
  return unwrapList(res.data);
}

export async function listProcedimentos() {
  const res = await apiClient.get('/radiologia/procedimentos/');
  return unwrapList(res.data);
}

export async function listPedidos(status?: string) {
  const q = status ? `?status=${encodeURIComponent(status)}` : '';
  const res = await apiClient.get(`/radiologia/pedidos/${q}`);
  return unwrapList(res.data) as PedidoExame[];
}

export async function listLaudos() {
  const res = await apiClient.get('/radiologia/laudos/');
  return unwrapList(res.data) as Laudo[];
}

export async function publicarMwl(pedidoId: number) {
  const res = await apiClient.post(`/radiologia/pedidos/${pedidoId}/publicar-mwl/`);
  return res.data as PedidoExame;
}

export async function cancelarPedido(pedidoId: number) {
  const res = await apiClient.post(`/radiologia/pedidos/${pedidoId}/cancelar/`);
  return res.data as PedidoExame;
}

export async function abrirLaudo(pedidoId: number) {
  const res = await apiClient.post(`/radiologia/pedidos/${pedidoId}/abrir-laudo/`);
  return res.data as Laudo;
}

export async function salvarLaudo(laudoId: number, payload: Partial<Laudo>) {
  const res = await apiClient.patch(`/radiologia/laudos/${laudoId}/`, payload);
  return res.data as Laudo;
}

export async function finalizarLaudo(laudoId: number, payload: Partial<Laudo> & { assinar?: boolean }) {
  const res = await apiClient.post(`/radiologia/laudos/${laudoId}/finalizar/`, payload);
  return res.data as Laudo;
}

export async function fetchLaudoPdf(laudoId: number): Promise<{ url?: string; blob?: Blob }> {
  const res = await apiClient.get(`/radiologia/laudos/${laudoId}/pdf/`, {
    responseType: 'blob',
    validateStatus: () => true,
  });
  const ct = String(res.headers['content-type'] || '');
  if (ct.includes('application/json')) {
    const text = await (res.data as Blob).text();
    const json = JSON.parse(text) as { url?: string };
    return { url: json.url };
  }
  return { blob: res.data as Blob };
}

export async function sincronizarImagensPedido(pedidoId: number) {
  const res = await apiClient.post(`/radiologia/pedidos/${pedidoId}/sincronizar-imagens/`);
  return res.data as PedidoExame;
}

export async function radiologiaHealth() {
  const res = await apiClient.get('/radiologia/health/');
  return res.data as { app: string; orthanc_url: string; orthanc_ok: boolean };
}
