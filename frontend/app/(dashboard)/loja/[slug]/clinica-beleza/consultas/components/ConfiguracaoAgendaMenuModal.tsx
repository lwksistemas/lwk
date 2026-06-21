"use client";

import { CalendarDays, FileText, MapPin, MessageCircle, RotateCcw, X } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";

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
    label: "Nomes de Agenda",
    description: "Tipos de agenda exibidos ao agendar (ex.: Consulta, Retorno)",
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
  if (!open) return null;

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
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 p-0 sm:p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-t-xl sm:rounded-xl shadow-xl w-full max-w-md sm:max-w-4xl sm:w-[calc(100vw-2rem)] max-h-[95vh] sm:max-h-[90vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-4 sm:px-6 py-4 border-b border-gray-200 dark:border-neutral-700 shrink-0">
          <div>
            <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">
              Configuração da Agenda
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 hidden sm:block">
              Escolha o que deseja configurar
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800 text-gray-500"
            aria-label="Fechar"
          >
            <X size={18} />
          </button>
        </div>

        <ul className="p-4 sm:p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 overflow-y-auto">
          {OPTIONS.map((opt) => {
            const Icon = opt.icon;
            return (
              <li key={opt.id} className="min-h-0">
                <button
                  type="button"
                  onClick={() => handleSelect(opt.id)}
                  className="w-full h-full flex items-start gap-3 p-4 rounded-xl text-left border border-gray-100 dark:border-neutral-800 hover:bg-gray-50 dark:hover:bg-neutral-800 hover:border-purple-200 dark:hover:border-purple-800 transition-colors"
                >
                  <span
                    className="flex w-10 h-10 shrink-0 items-center justify-center rounded-lg"
                    style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}18` }}
                  >
                    <Icon size={20} style={{ color: CLINICA_BELEZA_PRIMARY }} />
                  </span>
                  <span className="min-w-0">
                    <span className="block text-sm font-medium text-gray-900 dark:text-gray-100">{opt.label}</span>
                    <span className="block text-xs text-gray-500 dark:text-gray-400 mt-1 leading-snug">
                      {opt.description}
                    </span>
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
