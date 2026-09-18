"use client";

import { CalendarDays, FileText, MapPin, MessageCircle, RotateCcw } from "lucide-react";
import { ClinicaBelezaPortraitModal } from "@/components/clinica-beleza/ClinicaBelezaPortraitModal";

interface ConfiguracaoAgendaMenuModalProps {
  open: boolean;
  onClose: () => void;
  onLocais: () => void;
  onNomesAgenda: () => void;
  onMensagensWhatsApp: () => void;
  onNovoConvenio: () => void;
  onRetorno: () => void;
}

const OPTIONS = [
  {
    id: "locais",
    label: "Locais de Atendimento",
    description: "Salas, consultórios e locais onde o atendimento é realizado",
    icon: MapPin,
  },
  {
    id: "nomes",
    label: "Tipos de agenda",
    description: "Consulta e Retorno vêm no sistema; cadastre outros tipos se precisar",
    icon: CalendarDays,
  },
  {
    id: "whatsapp",
    label: "Mensagem WhatsApp",
    description: "Texto personalizado enviado com o link de confirmação do agendamento",
    icon: MessageCircle,
  },
  {
    id: "retorno",
    label: "Retorno gratuito",
    description: "Retorno por consulta ou por procedimento — prazo definido pelo administrador",
    icon: RotateCcw,
  },
  {
    id: "convenio",
    label: "Cadastrar convênio",
    description: "Gerenciar convênios da clínica — cadastre, visualize e exclua",
    icon: FileText,
  },
] as const;

export function ConfiguracaoAgendaMenuModal({
  open,
  onClose,
  onLocais,
  onNomesAgenda,
  onMensagensWhatsApp,
  onNovoConvenio,
  onRetorno,
}: ConfiguracaoAgendaMenuModalProps) {
  const handlers: Record<(typeof OPTIONS)[number]["id"], () => void> = {
    locais: onLocais,
    nomes: onNomesAgenda,
    whatsapp: onMensagensWhatsApp,
    retorno: onRetorno,
    convenio: onNovoConvenio,
  };

  const handleSelect = (id: (typeof OPTIONS)[number]["id"]) => {
    onClose();
    handlers[id]();
  };

  return (
    <ClinicaBelezaPortraitModal
      open={open}
      layout="landscape"
      onClose={onClose}
      title="Configuração da Agenda"
      subtitle="Escolha o que deseja configurar"
    >
      <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {OPTIONS.map((opt) => {
          const Icon = opt.icon;
          return (
            <li key={opt.id}>
              <button
                type="button"
                onClick={() => handleSelect(opt.id)}
                className="w-full h-full flex items-center gap-3 p-3.5 rounded-xl text-left border border-gray-100 dark:border-neutral-800 hover:bg-gray-50 dark:hover:bg-neutral-800 hover:border-purple-200 dark:hover:border-purple-800 transition-colors"
              >
                <span
                  className="flex w-11 h-11 shrink-0 items-center justify-center rounded-xl"
                  style={{ backgroundColor: "color-mix(in srgb, var(--cb-primary, #8B3D52) 9%, transparent)" }}
                >
                  <Icon size={22} style={{ color: "var(--cb-primary, #8B3D52)" }} />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {opt.label}
                  </span>
                  <span className="block text-xs text-gray-500 dark:text-gray-400 mt-1 leading-snug">
                    {opt.description}
                  </span>
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </ClinicaBelezaPortraitModal>
  );
}
