"use client";

import { useEffect, useMemo, useState } from "react";
import { Loader2 } from "lucide-react";
import { clinicaBelezaFetch, parseClinicaBelezaListResponse, parseClinicaBelezaResponseBody } from "@/lib/clinica-beleza-api";
import { saveClinicaBelezaEntity } from "@/lib/clinica-beleza-crud";
import {
  dividirValorProtocolo,
  formatarValorProtocolo,
} from "./protocolos-page-utils";
import {
  FORM_INPUT_CLASS,
  FORM_LABEL_CLASS,
  type Protocol,
} from "./protocolos-page-types";

interface Opcao {
  id: number;
  nome?: string;
  name?: string;
}

interface ProtocoloAgendarModalProps {
  protocol: Protocol;
  onClose: () => void;
  onSaved: (mensagem: string) => void;
}

export function ProtocoloAgendarModal({ protocol, onClose, onSaved }: ProtocoloAgendarModalProps) {
  const [pacienteBusca, setPacienteBusca] = useState("");
  const [pacientes, setPacientes] = useState<Opcao[]>([]);
  const [patient, setPatient] = useState("");
  const [profissionais, setProfissionais] = useState<Opcao[]>([]);
  const [professional, setProfessional] = useState("");
  const [locais, setLocais] = useState<Opcao[]>([]);
  const [local, setLocal] = useState("");
  const [dataInicio, setDataInicio] = useState("");
  const [forma, setForma] = useState<"POR_CONSULTA" | "TOTAL">("POR_CONSULTA");
  const [erro, setErro] = useState("");
  const [salvando, setSalvando] = useState(false);

  useEffect(() => {
    let ativo = true;
    void (async () => {
      const [resProf, resLocal] = await Promise.all([
        clinicaBelezaFetch("/professionals/?scheduling=true&all=1"),
        clinicaBelezaFetch("/locais-atendimento/?all=1"),
      ]);
      const [dadosProf, dadosLocal] = await Promise.all([
        parseClinicaBelezaResponseBody(resProf),
        parseClinicaBelezaResponseBody(resLocal),
      ]);
      if (!ativo) return;
      setProfissionais(parseClinicaBelezaListResponse<Opcao>(dadosProf));
      setLocais(parseClinicaBelezaListResponse<Opcao>(dadosLocal));
    })();
    return () => {
      ativo = false;
    };
  }, []);

  useEffect(() => {
    const termo = pacienteBusca.trim();
    if (termo.length < 2) return;
    const timer = window.setTimeout(() => {
      void (async () => {
        const res = await clinicaBelezaFetch(`/patients/?search=${encodeURIComponent(termo)}&page_size=10`);
        const dados = await parseClinicaBelezaResponseBody(res);
        setPacientes(parseClinicaBelezaListResponse<Opcao>(dados));
      })();
    }, 300);
    return () => window.clearTimeout(timer);
  }, [pacienteBusca]);

  const sessoes = protocol.sessoes || 1;
  const valor = Number(protocol.valor || 0);
  const partes = useMemo(
    () => dividirValorProtocolo(valor, sessoes, forma),
    [valor, sessoes, forma],
  );
  const resumo =
    forma === "TOTAL"
      ? `${formatarValorProtocolo(valor)} na primeira sessão. As demais não geram nova cobrança do protocolo.`
      : partes.every((parte) => parte === partes[0])
        ? `${sessoes}x de ${formatarValorProtocolo(partes[0] || 0)}`
        : partes.map((parte, i) => `Sessão ${i + 1}: ${formatarValorProtocolo(parte)}`).join(" · ");

  const agendar = async () => {
    if (!patient || !professional || !local || !dataInicio) {
      setErro("Paciente, profissional, local e a data da primeira sessão são obrigatórios.");
      return;
    }
    setSalvando(true);
    setErro("");
    try {
      const resultado = (await saveClinicaBelezaEntity(`/protocolos/${protocol.id}/agendar/`, "POST", {
        patient: Number(patient),
        professional: Number(professional),
        local_atendimento: Number(local),
        data_inicio: dataInicio.length === 16 ? `${dataInicio}:00` : dataInicio,
        forma_cobranca: forma,
      })) as { agendamentos?: { id: number }[] };
      const quantidade = resultado.agendamentos?.length || sessoes;
      onSaved(`${quantidade} sessões criadas na agenda.`);
    } catch (e: unknown) {
      const dados = e as { detail?: string; conflitos?: { motivo?: string }[] };
      const linhas = (dados.conflitos || []).map((item) => item.motivo).filter(Boolean);
      setErro(linhas.length > 0 ? linhas.join(" ") : dados.detail || "Não foi possível agendar o protocolo.");
    } finally {
      setSalvando(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-lg rounded-xl bg-white dark:bg-neutral-900 shadow-xl p-5 space-y-4 max-h-[90vh] overflow-y-auto">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Agendar protocolo</h2>
          <p className="text-sm text-gray-500 mt-1">{protocol.nome}</p>
        </div>
        {erro && (
          <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 text-sm">
            {erro}
          </div>
        )}
        <div>
          <label className={FORM_LABEL_CLASS}>Paciente *</label>
          <input
            value={pacienteBusca}
            onChange={(e) => setPacienteBusca(e.target.value)}
            className={FORM_INPUT_CLASS}
            placeholder="Buscar pelo nome"
          />
          {pacientes.length > 0 && (
            <select
              value={patient}
              onChange={(e) => setPatient(e.target.value)}
              className={`${FORM_INPUT_CLASS} mt-2`}
            >
              <option value="">Selecione...</option>
              {pacientes.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.nome || item.name}
                </option>
              ))}
            </select>
          )}
        </div>
        <div>
          <label className={FORM_LABEL_CLASS}>Profissional *</label>
          <select value={professional} onChange={(e) => setProfessional(e.target.value)} className={FORM_INPUT_CLASS}>
            <option value="">Selecione...</option>
            {profissionais.map((item) => (
              <option key={item.id} value={item.id}>
                {item.nome || item.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className={FORM_LABEL_CLASS}>Local *</label>
          <select value={local} onChange={(e) => setLocal(e.target.value)} className={FORM_INPUT_CLASS}>
            <option value="">Selecione...</option>
            {locais.map((item) => (
              <option key={item.id} value={item.id}>
                {item.nome || item.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className={FORM_LABEL_CLASS}>Primeira sessão *</label>
          <input
            type="datetime-local"
            value={dataInicio}
            onChange={(e) => setDataInicio(e.target.value)}
            className={FORM_INPUT_CLASS}
          />
        </div>
        <fieldset className="space-y-2">
          <legend className={FORM_LABEL_CLASS}>Cobrança *</legend>
          <label className="flex items-start gap-2 text-sm text-gray-800 dark:text-gray-200">
            <input type="radio" checked={forma === "POR_CONSULTA"} onChange={() => setForma("POR_CONSULTA")} />
            Por consulta — divide o valor entre as sessões
          </label>
          <label className="flex items-start gap-2 text-sm text-gray-800 dark:text-gray-200">
            <input type="radio" checked={forma === "TOTAL"} onChange={() => setForma("TOTAL")} />
            Valor total — cobra o pacote na primeira sessão
          </label>
          <p className="text-sm text-gray-600 dark:text-gray-300">{resumo}</p>
        </fieldset>
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm rounded-lg border border-gray-300">
            Cancelar
          </button>
          <button
            type="button"
            onClick={() => void agendar()}
            disabled={salvando}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm rounded-lg text-white disabled:opacity-60"
            style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
          >
            {salvando && <Loader2 size={16} className="animate-spin" />}
            Criar sessões
          </button>
        </div>
      </div>
    </div>
  );
}
