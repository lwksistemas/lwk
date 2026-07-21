import { getClinicaBelezaBaseUrl } from "./fetch";
import type { MemedApi } from "./client-memed";
import type { ProntuarioApi } from "./client-prontuario";
import { consultasApi } from "./client-consultas";
import {
  anamneseApi,
  campanhasApi,
  conveniosApi,
  documentosApi,
  patientsApi,
  proceduresApi,
  professionalsApi,
  templatesApi,
} from "./client-entities";
import { estoqueApi, financeiroApi, locaisAtendimentoApi, lojaApi, nomesAgendaApi, retornoApi } from "./client-ops";
import { cbDelete, cbGet, cbGetList, cbPatch, cbPost, cbPut } from "./client-http";

const loadMemedApi = () => import("./client-memed").then((m) => m.memedApi);
const loadProntuarioApi = () => import("./client-prontuario").then((m) => m.prontuarioApi);

export class ClinicaBelezaAPI {
  static getList = cbGetList;
  static get = cbGet;
  static post = cbPost;
  static put = cbPut;
  static patch = cbPatch;
  static delete = cbDelete;

  static consultas = consultasApi;
  static anamnese = anamneseApi;
  static patients = patientsApi;
  static professionals = professionalsApi;
  static loja = lojaApi;
  static financeiro = financeiroApi;
  static estoque = estoqueApi;

  static memed: MemedApi = {
    timbrado: {
      get: () => loadMemedApi().then((m) => m.timbrado.get()),
    },
    status: () => loadMemedApi().then((m) => m.status()),
    salvarPrescricao: (consultaId, data) => loadMemedApi().then((m) => m.salvarPrescricao(consultaId, data)),
    listarPrescricoesConsulta: (consultaId) =>
      loadMemedApi().then((m) => m.listarPrescricoesConsulta(consultaId)),
    listarPrescricoesPaciente: (patientId) =>
      loadMemedApi().then((m) => m.listarPrescricoesPaciente(patientId)),
    obterPdf: (prescricaoId) => loadMemedApi().then((m) => m.obterPdf(prescricaoId)),
    excluirPrescricao: (consultaId, prescricaoId) =>
      loadMemedApi().then((m) => m.excluirPrescricao(consultaId, prescricaoId)),
  };

  static templates = templatesApi;
  static documentos = documentosApi;

  static prontuario: ProntuarioApi = {
    get: (patientId, secao) => loadProntuarioApi().then((m) => m.get(patientId, secao)),
    pdfUrl: (patientId, secao) => {
      const base = getClinicaBelezaBaseUrl();
      const query = secao ? `?secao=${secao}` : "";
      return `${base}/patients/${patientId}/prontuario/pdf/${query}`;
    },
  };

  static locaisAtendimento = locaisAtendimentoApi;
  static nomesAgenda = nomesAgendaApi;
  static retorno = retornoApi;
  static campanhas = campanhasApi;
  static procedures = proceduresApi;
  static convenios = conveniosApi;

  static payments = {
    enviarRecibo: (paymentId: number, canal: 'email' | 'whatsapp') =>
      ClinicaBelezaAPI.post(`/payments/${paymentId}/enviar-recibo/`, { canal }),
  };
}
