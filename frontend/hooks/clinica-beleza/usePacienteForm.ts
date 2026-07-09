"use client";

import { useEffect, useState } from "react";
import { saveClinicaBelezaEntity } from "@/lib/clinica-beleza-crud";
import { entityName } from "@/lib/clinica-beleza-entities";
import { applyTelefoneInternacionalPayload, formatCep, toUpperCase } from "@/lib/format-br";
import { consultaCep } from "@/lib/consulta-cep";
import { salvarPacientesOffline } from "@/lib/offline-db";
import { ClinicaBelezaAPI, type ConvenioItem } from "@/lib/clinica-beleza-api";
import { findConvenioParticular } from "@/lib/convenio-precos";
import { useOfflineSave } from "@/hooks/clinica-beleza/useOfflineSave";
import { useToast } from "@/components/ui/Toast";
import {
  PACIENTE_EMPTY_FORM,
  type PacienteFormState,
} from "@/components/clinica-beleza/paciente-cadastro/paciente-cadastro-types";
import {
  montarEnderecoPaciente,
  patientToForm,
  type Patient,
} from "@/components/clinica-beleza/pacientes-page/lib/paciente-form-utils";

export interface UsePacienteFormOptions {
  isNovo: boolean;
  editIdParam: string | null;
  isFormView: boolean;
  list: Patient[];
  setList: (list: Patient[]) => void;
  load: () => void;
  voltarLista: () => void;
}

export function usePacienteForm({
  isNovo,
  editIdParam,
  isFormView,
  list,
  setList,
  load,
  voltarLista,
}: UsePacienteFormOptions) {
  const toast = useToast();
  const [editing, setEditing] = useState<Patient | null>(null);
  const [form, setForm] = useState<PacienteFormState>(PACIENTE_EMPTY_FORM);
  const [error, setError] = useState("");
  const [buscarCepLoading, setBuscarCepLoading] = useState(false);
  const [convenios, setConvenios] = useState<ConvenioItem[]>([]);

  const { save: offlineSave, saving } = useOfflineSave<Patient>({
    entityType: "paciente",
    saveOnline: async (body, ed) => {
      if (ed) {
        await saveClinicaBelezaEntity(`/patients/${ed.id}/`, "PUT", body);
      } else {
        await saveClinicaBelezaEntity("/patients/", "POST", body);
      }
    },
    list,
    setList,
    saveOffline: salvarPacientesOffline,
    buildNewEntity: (body, tempId) => ({
      id: tempId,
      ...(body as Omit<Patient, "id">),
    }),
    duplicatePredicate: (p) =>
      entityName(p).toLowerCase() === form.name.trim().toLowerCase(),
  });

  useEffect(() => {
    if (isNovo) {
      setEditing(null);
      setForm(PACIENTE_EMPTY_FORM);
      setError("");
      return;
    }
    if (!editIdParam) return;
    const found = list.find((x) => String(x.id) === editIdParam);
    if (found) {
      setEditing(found);
      setForm(patientToForm(found));
      setError("");
      return;
    }
    let cancelled = false;
    ClinicaBelezaAPI.patients
      .get(Number(editIdParam))
      .then((fetched) => {
        if (!cancelled) {
          setEditing(fetched as Patient);
          setForm(patientToForm(fetched as Patient));
          setError("");
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [isNovo, editIdParam, list]);

  useEffect(() => {
    if (!isFormView) return;
    ClinicaBelezaAPI.convenios
      .list()
      .then((rows) => setConvenios(Array.isArray(rows) ? rows : []))
      .catch(() => setConvenios([]));
  }, [isFormView]);

  useEffect(() => {
    if (!isFormView) return;
    const particular = findConvenioParticular(convenios);
    if (!particular) return;
    setForm((f) => {
      if (isNovo) return { ...f, convenio: particular.id };
      if (f.convenio === "") return { ...f, convenio: particular.id };
      return f;
    });
  }, [isFormView, isNovo, convenios]);

  const handleCepChange = (value: string) =>
    setForm((f) => ({ ...f, cep: formatCep(value) }));

  const handleBuscarCep = async () => {
    const cep = form.cep.replace(/\D/g, "");
    if (cep.length !== 8) {
      setError("Informe um CEP válido com 8 dígitos.");
      return;
    }
    setBuscarCepLoading(true);
    setError("");
    try {
      const endereco = await consultaCep(form.cep);
      if (endereco) {
        setForm((f) => ({
          ...f,
          logradouro: toUpperCase(endereco.logradouro),
          bairro: toUpperCase(endereco.bairro),
          cidade: toUpperCase(endereco.cidade),
          uf: endereco.uf.toUpperCase(),
        }));
      } else {
        setError("CEP não encontrado. Verifique o número ou tente novamente.");
      }
    } finally {
      setBuscarCepLoading(false);
    }
  };

  const save = async () => {
    if (!form.name.trim()) {
      setError("Nome é obrigatório.");
      return;
    }
    setError("");
    const body = applyTelefoneInternacionalPayload({
      name: form.name.trim(),
      phone: form.phone.trim() || null,
      email: form.email.trim() || null,
      cpf: form.cpf.trim() || null,
      birth_date: form.birth_date || null,
      address: montarEnderecoPaciente(form) || null,
      cidade: form.cidade.trim() || null,
      estado: form.uf.trim().toUpperCase() || null,
      notes: form.notes.trim() || null,
      active: true,
      allow_whatsapp: form.allow_whatsapp,
      convenio: form.convenio ? Number(form.convenio) : null,
      foto_url: form.foto_url.trim() || null,
    });

    const result = await offlineSave(body, editing);
    if (!result.ok) {
      if (result.error) setError(result.error);
      return;
    }
    if (result.offline) toast.warning(result.message);
    voltarLista();
    load();
  };

  return {
    editing,
    form,
    setForm,
    error,
    saving,
    convenios,
    buscarCepLoading,
    handleCepChange,
    handleBuscarCep,
    save,
  };
}
