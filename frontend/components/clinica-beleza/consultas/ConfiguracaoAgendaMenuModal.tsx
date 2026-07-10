"use client";

import { CalendarDays, FileText, MapPin, MessageCircle, RotateCcw, X } from "lucide-react";

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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-2xl shadow-xl w-full max-w-[22rem] max-h-[min(90vh,640px)] flex flex-col overflow-hidden">
        <div className="flex items-start justify-between gap-3 px-5 py-4 border-b border-gray-200 dark:border-neutral-700 shrink-0">
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 leading-tight">
              Configuração da Agenda
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Escolha o que deseja configurar
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800 text-gray-500 shrink-0"
            aria-label="Fechar"
          >
            <X size={18} />
          </button>
        </div>

        <ul className="flex-1 min-h-0 overflow-y-auto overscroll-contain p-3 space-y-2">
          {OPTIONS.map((opt) => {
            const Icon = opt.icon;
            return (
              <li key={opt.id}>
                <button
                  type="button"
                  onClick={() => handleSelect(opt.id)}
                  className="w-full flex items-center gap-3 p-3.5 rounded-xl text-left border border-gray-100 dark:border-neutral-800 hover:bg-gray-50 dark:hover:bg-neutral-800 hover:border-purple-200 dark:hover:border-purple-800 transition-colors"
                >
                  <span
                    className="flex w-11 h-11 shrink-0 items-center justify-center rounded-xl"
                    style={{ backgroundColor: 'color-mix(in srgb, var(--cb-primary, #8B3D52) 9%, transparent)' }}
                  >
                    <Icon size={22} style={{ color: 'var(--cb-primary, #8B3D52)' }} />
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
      </div>
    </div>
  );
}
