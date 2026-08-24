import apiClient from '@/lib/api-client';
import type {
  Consulta,
  DiaHorariosLivres,
  Paciente,
  PacienteAnexo,
  PacienteLista,
  CaixaDia,
  ConfiguracaoConsultorio,
  Evolucao,
  GuiaTiss,
  LoteTiss,
  Prescricao,
  PrescricaoItem,
  RelatorioResposta,
  UsuarioConsultorio,
  StatusConsulta,
  Tarefa,
  TipoRelatorio,
  EspecialidadeEquipe,
  FuncionarioLoja,
  ProfissionalEquipe,
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

export async function getConsulta(id: number) {
  try {
    const res = await apiClient.get(`/clinica-geral/consultas/${id}/`);
    return res.data as Consulta;
  } catch {
    return null;
  }
}

export async function listConsultas(data: string) {
  const res = await apiClient.get(`/clinica-geral/consultas/?data=${encodeURIComponent(data)}`);
  return unwrapList(res.data) as Consulta[];
}

export async function listConsultasPaciente(pacienteId: number) {
  const res = await apiClient.get(`/clinica-geral/consultas/?paciente=${pacienteId}`);
  return unwrapList(res.data) as Consulta[];
}

export async function listAnexosPaciente(pacienteId: number) {
  const res = await apiClient.get(`/clinica-geral/anexos/?paciente=${pacienteId}`);
  return unwrapList(res.data) as PacienteAnexo[];
}

export async function createAnexoPaciente(paciente: number, nome: string, url: string) {
  const res = await apiClient.post('/clinica-geral/anexos/', { paciente, nome, url });
  return res.data as PacienteAnexo;
}

export async function deleteAnexoPaciente(id: number) {
  await apiClient.delete(`/clinica-geral/anexos/${id}/`);
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

export async function getUsuarioConsultorio() {
  const res = await apiClient.get('/clinica-geral/me/');
  return res.data as UsuarioConsultorio;
}

export async function saveUsuarioConsultorio(payload: Partial<UsuarioConsultorio>) {
  const res = await apiClient.patch('/clinica-geral/me/', payload);
  return res.data as UsuarioConsultorio;
}

export async function getConfiguracao() {
  const res = await apiClient.get('/clinica-geral/configuracao/atual/');
  return res.data as ConfiguracaoConsultorio;
}

export async function saveConfiguracao(payload: Partial<ConfiguracaoConsultorio>) {
  const res = await apiClient.patch('/clinica-geral/configuracao/atual/', payload);
  return res.data as ConfiguracaoConsultorio;
}

export async function checkinConsulta(id: number) {
  const res = await apiClient.post(`/clinica-geral/consultas/${id}/checkin/`);
  return res.data as Consulta;
}

export async function abrirTele(id: number) {
  const res = await apiClient.post(`/clinica-geral/consultas/${id}/abrir-tele/`);
  return res.data as Consulta & { tele_minutos_mes?: number; teto_tele_minutos?: number };
}

export async function enviarTele(id: number, frontendBase?: string) {
  const res = await apiClient.post(`/clinica-geral/consultas/${id}/enviar-tele/`, {
    frontend_base: frontendBase || (typeof window !== 'undefined' ? window.location.origin : ''),
  });
  return res.data as Consulta & { tele_minutos_mes?: number; teto_tele_minutos?: number; enviado?: boolean };
}

export async function registrarTele(id: number, minutos: number) {
  const res = await apiClient.post(`/clinica-geral/consultas/${id}/registrar-tele/`, { minutos });
  return res.data as Consulta;
}

export async function getEvolucaoDaConsulta(consultaId: number) {
  const res = await apiClient.get(`/clinica-geral/evolucoes/?consulta=${consultaId}`);
  return unwrapList(res.data)[0] as Evolucao | undefined;
}

export async function saveEvolucao(payload: Partial<Evolucao> & { consulta: number; paciente: number }) {
  if (payload.id) {
    const res = await apiClient.patch(`/clinica-geral/evolucoes/${payload.id}/`, payload);
    return res.data as Evolucao;
  }
  const res = await apiClient.post('/clinica-geral/evolucoes/', payload);
  return res.data as Evolucao;
}

export async function listPrescricoes(consultaId: number) {
  const res = await apiClient.get(`/clinica-geral/prescricoes/?consulta=${consultaId}`);
  return unwrapList(res.data) as Prescricao[];
}

export async function createPrescricao(consulta: number, paciente: number, itens: PrescricaoItem[]) {
  const res = await apiClient.post('/clinica-geral/prescricoes/', { consulta, paciente, itens });
  return res.data as Prescricao;
}

export function receitaPdfUrl(id: number) {
  return `/clinica-geral/prescricoes/${id}/pdf/`;
}

export async function getProntuario(pacienteId: number) {
  const res = await apiClient.get(`/clinica-geral/pacientes/${pacienteId}/prontuario/`);
  return res.data as { paciente: Paciente; evolucoes: Evolucao[]; prescricoes: Prescricao[] };
}

export function evolucaoPdfUrl(id: number) {
  return `/clinica-geral/evolucoes/${id}/pdf/`;
}

export async function listLotesTiss() {
  const res = await apiClient.get('/clinica-geral/lotes-tiss/');
  return unwrapList(res.data) as LoteTiss[];
}

export async function createLoteTiss(competencia: string) {
  const res = await apiClient.post('/clinica-geral/lotes-tiss/', { competencia, status: 'aberto' });
  return res.data as LoteTiss;
}

export async function listGuiasTiss(loteId?: number) {
  const qs = loteId ? `?lote=${loteId}` : '';
  const res = await apiClient.get(`/clinica-geral/guias-tiss/${qs}`);
  return unwrapList(res.data) as GuiaTiss[];
}

export async function createGuiaTiss(consulta: number, lote: number | null, valor?: string | null) {
  const res = await apiClient.post('/clinica-geral/guias-tiss/', { consulta, lote, valor: valor || null });
  return res.data as GuiaTiss;
}

export function guiaPdfUrl(id: number) {
  return `/clinica-geral/guias-tiss/${id}/pdf/`;
}

export async function getCaixaDia(data: string) {
  const res = await apiClient.get(`/clinica-geral/caixa/dia/?data=${encodeURIComponent(data)}`);
  return res.data as CaixaDia;
}

export async function fecharCaixa(data: string, observacoes = '') {
  const res = await apiClient.post('/clinica-geral/caixa/dia/', { data, observacoes });
  return res.data;
}

export async function openPdf(path: string) {
  const res = await apiClient.get(path, { responseType: 'blob' });
  const url = URL.createObjectURL(res.data);
  window.open(url, '_blank', 'noopener');
}

export async function fetchRelatorio(tipo: TipoRelatorio, de: string, ate: string) {
  const params = new URLSearchParams({ tipo, de, ate });
  const res = await apiClient.get(`/clinica-geral/relatorios/?${params.toString()}`);
  return res.data as RelatorioResposta;
}

export async function listEspecialidades() {
  const res = await apiClient.get('/clinica-geral/especialidades/');
  return unwrapList(res.data) as EspecialidadeEquipe[];
}

export async function createEspecialidade(nome: string) {
  const res = await apiClient.post('/clinica-geral/especialidades/', { nome });
  return res.data as EspecialidadeEquipe;
}

export async function updateEspecialidade(id: number, nome: string) {
  const res = await apiClient.patch(`/clinica-geral/especialidades/${id}/`, { nome });
  return res.data as EspecialidadeEquipe;
}

export async function deleteEspecialidade(id: number) {
  await apiClient.delete(`/clinica-geral/especialidades/${id}/`);
}

export async function createProfissional(payload: Partial<ProfissionalEquipe>) {
  const res = await apiClient.post('/clinica-geral/profissionais/', payload);
  return res.data as ProfissionalEquipe;
}

export async function updateProfissional(id: number, payload: Partial<ProfissionalEquipe>) {
  const res = await apiClient.patch(`/clinica-geral/profissionais/${id}/`, payload);
  return res.data as ProfissionalEquipe;
}

export async function deleteProfissional(id: number) {
  await apiClient.delete(`/clinica-geral/profissionais/${id}/`);
}

export async function listFuncionarios() {
  const res = await apiClient.get('/clinica-geral/funcionarios/');
  return unwrapList(res.data) as FuncionarioLoja[];
}

export async function createFuncionario(payload: Partial<FuncionarioLoja>) {
  const res = await apiClient.post('/clinica-geral/funcionarios/', payload);
  return res.data as FuncionarioLoja;
}

export async function updateFuncionario(id: number, payload: Partial<FuncionarioLoja>) {
  const res = await apiClient.patch(`/clinica-geral/funcionarios/${id}/`, payload);
  return res.data as FuncionarioLoja;
}

export async function deleteFuncionario(id: number) {
  await apiClient.delete(`/clinica-geral/funcionarios/${id}/`);
}
