"use client";

import { CalendarDays, FileText, MapPin, MessageCircle, X } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";

interface ConfiguracaoAgendaMenuModalProps {
  open: boolean;
  onClose: () => void;
  onLocais: () => void;
  onNomesAgenda: () => void;
  onMensagensWhatsApp: () => void;
  onNovoConvenio: () => void;
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
    id: "convenio",
    label: "Cadastrar convênio",
    description: "Novo convênio — informe o nome; o código será gerado automaticamente",
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
}: ConfiguracaoAgendaMenuModalProps) {
  if (!open) return null;

  const handlers: Record<(typeof OPTIONS)[number]["id"], () => void> = {
    locais: onLocais,
    nomes: onNomesAgenda,
    whatsapp: onMensagensWhatsApp,
    convenio: onNovoConvenio,
  };

  const handleSelect = (id: (typeof OPTIONS)[number]["id"]) => {
    onClose();
    handlers[id]();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-neutral-700">
          <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">Configuração da Agenda</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800 text-gray-500"
            aria-label="Fechar"
          >
            <X size={18} />
          </button>
        </div>

        <ul className="p-3 space-y-1">
          {OPTIONS.map((opt) => {
            const Icon = opt.icon;
            return (
              <li key={opt.id}>
                <button
                  type="button"
                  onClick={() => handleSelect(opt.id)}
                  className="w-full flex items-start gap-3 p-3 rounded-lg text-left hover:bg-gray-50 dark:hover:bg-neutral-800 transition-colors"
                >
                  <span
                    className="flex w-9 h-9 shrink-0 items-center justify-center rounded-lg"
                    style={{ backgroundColor: `${CLINICA_BELEZA_PRIMARY}18` }}
                  >
                    <Icon size={18} style={{ color: CLINICA_BELEZA_PRIMARY }} />
                  </span>
                  <span className="min-w-0">
                    <span className="block text-sm font-medium text-gray-900 dark:text-gray-100">{opt.label}</span>
                    <span className="block text-xs text-gray-500 dark:text-gray-400 mt-0.5">{opt.description}</span>
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
