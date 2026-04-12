'use client';

import { Building2, Briefcase, Mail, Phone } from 'lucide-react';
import { ModalWrapper } from './ContatoFormModal';

interface Contato {
  id: number;
  nome: string;
  email?: string;
  telefone?: string;
  cargo?: string;
  conta_nome?: string;
  observacoes?: string;
}

interface ContatoViewModalProps {
  contato: Contato;
  onClose: () => void;
  onEdit: () => void;
}

export function ContatoViewModal({ contato, onClose, onEdit }: ContatoViewModalProps) {
  return (
    <ModalWrapper title="Detalhes do Contato" onClose={onClose}>
      <div className="space-y-4">
        <div className="flex items-center gap-3 pb-4 border-b border-gray-200 dark:border-gray-700">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-[#06a59a] to-[#0d9dda] flex items-center justify-center text-white font-bold text-lg">
            {contato.nome.charAt(0).toUpperCase()}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{contato.nome}</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">{contato.cargo || 'Sem cargo definido'}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <InfoItem icon={<Building2 size={18} />} label="Conta" value={contato.conta_nome} />
          {contato.cargo && <InfoItem icon={<Briefcase size={18} />} label="Cargo" value={contato.cargo} />}
          {contato.email && <InfoItem icon={<Mail size={18} />} label="Email" value={contato.email} />}
          {contato.telefone && <InfoItem icon={<Phone size={18} />} label="Telefone" value={contato.telefone} />}
        </div>

        {contato.observacoes && (
          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Observações</p>
            <p className="text-sm text-gray-900 dark:text-white whitespace-pre-wrap">{contato.observacoes}</p>
          </div>
        )}

        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={onClose} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            Fechar
          </button>
          <button type="button" onClick={onEdit} className="px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded transition-colors">
            Editar
          </button>
        </div>
      </div>
    </ModalWrapper>
  );
}

function InfoItem({ icon, label, value }: { icon: React.ReactNode; label: string; value?: string }) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-2">
      <span className="text-gray-400 mt-0.5">{icon}</span>
      <div>
        <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
        <p className="text-sm text-gray-900 dark:text-white">{value}</p>
      </div>
    </div>
  );
}
