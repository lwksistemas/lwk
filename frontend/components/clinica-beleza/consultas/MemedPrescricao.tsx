"use client";

/**
 * Integração Memed — prescrição digital (Receituário e Exames).
 * Carrega sob demanda; lógica em `memed/useMemedPrescricao`.
 */

import { forwardRef, useImperativeHandle } from "react";
import { useMemedPrescricao } from "./memed/useMemedPrescricao";

export interface MemedPrescricaoHandle {
  abrir: () => Promise<void>;
  fechar: () => void;
}

interface MemedPrescricaoProps {
  consultaId: number;
  professionalId?: number | null;
  patientId: number;
  patientName: string;
  onPrescricaoRegistrada?: () => void;
}

const MemedPrescricao = forwardRef<MemedPrescricaoHandle, MemedPrescricaoProps>(
  ({ consultaId, professionalId, patientId, patientName, onPrescricaoRegistrada }, ref) => {
    const { abrir, fechar } = useMemedPrescricao({
      consultaId,
      professionalId,
      patientId,
      patientName,
      onPrescricaoRegistrada,
    });

    useImperativeHandle(ref, () => ({ abrir, fechar }), [abrir, fechar]);
    return null;
  },
);

MemedPrescricao.displayName = "MemedPrescricao";

export default MemedPrescricao;
