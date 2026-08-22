import apiClient from '@/lib/api-client';
import type {
  Consulta,
  DiaHorariosLivres,
  Paciente,
  PacienteLista,
  StatusConsulta,
  Tarefa,
} from '@/lib/clinica-geral-types';

function unwrapList<T>(data: T[] | { results?: T[] }): T[] {
  return Array.isArray(data) ? data : data.results ?? [];
}

export async function listPacientes(opts?: { letra?: string; q?: string }) {
  const params = new URLSearchParams();
  if (opts?.letra && opts.letra !== 'TODOS') params.set('letra', opts.letra);
  if (opts?.q) params.set('q', opts.q);
  const qs = params.toString();
  const res = await apiClient.get(`/clinica-geral/pacientes/${qs ? `?${qs}` : ''}`);
  return unwrapList(res.data) as PacienteLista[];
}

export async function getPaciente(id: number) {
  const res = await apiClient.get(`/clinica-geral/pacientes/${id}/`);
  return res.data as Paciente;
}

export async function createPaciente(payload: Partial<Paciente>) {
  const res = await apiClient.post('/clinica-geral/pacientes/', payload);
  return res.data as Paciente;
}

export async function updatePaciente(id: number, payload: Partial<Paciente>) {
  const res = await apiClient.patch(`/clinica-geral/pacientes/${id}/`, payload);
  return res.data as Paciente;
}

export async function archivePaciente(id: number) {
  await apiClient.delete(`/clinica-geral/pacientes/${id}/`);
}

export async function listConsultas(data: string) {
  const res = await apiClient.get(`/clinica-geral/consultas/?data=${encodeURIComponent(data)}`);
  return unwrapList(res.data) as Consulta[];
}

export async function createConsulta(payload: Partial<Consulta>) {
  const res = await apiClient.post('/clinica-geral/consultas/', payload);
  return res.data as Consulta;
}

export async function updateConsulta(id: number, payload: Partial<Consulta>) {
  const res = await apiClient.patch(`/clinica-geral/consultas/${id}/`, payload);
  return res.data as Consulta;
}

export async function updateConsultaStatus(id: number, status: StatusConsulta) {
  return updateConsulta(id, { status });
}

export async function cancelarConsulta(id: number) {
  await apiClient.delete(`/clinica-geral/consultas/${id}/`);
}

export async function listHorariosLivres(data: string) {
  const res = await apiClient.get(
    `/clinica-geral/consultas/horarios-livres/?data=${encodeURIComponent(data)}`,
  );
  return (res.data?.dias ?? []) as DiaHorariosLivres[];
}

export async function recepcionarConsulta(id: number, payload: Partial<Paciente> & { convenio?: string }) {
  const res = await apiClient.post(`/clinica-geral/consultas/${id}/recepcionar/`, payload);
  return res.data as Consulta;
}

export async function listTarefas(data: string) {
  const res = await apiClient.get(`/clinica-geral/tarefas/?data=${encodeURIComponent(data)}`);
  return unwrapList(res.data) as Tarefa[];
}

export async function createTarefa(data: string, texto: string) {
  const res = await apiClient.post('/clinica-geral/tarefas/', { data, texto, concluida: false });
  return res.data as Tarefa;
}

export async function toggleTarefa(tarefa: Tarefa) {
  const res = await apiClient.patch(`/clinica-geral/tarefas/${tarefa.id}/`, { concluida: !tarefa.concluida });
  return res.data as Tarefa;
}

export async function deleteTarefa(id: number) {
  await apiClient.delete(`/clinica-geral/tarefas/${id}/`);
}
