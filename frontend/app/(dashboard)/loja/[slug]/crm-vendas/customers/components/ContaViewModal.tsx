'use client';

import { Mail, Phone, MapPin, Tag, Building2 } from 'lucide-react';
import { ModalShell } from './ContaFormModal';

const TIPO_LABELS: Record<string, string> = {
  cliente: 'Cliente',
  prestadora: 'Prestadora de Serviço',
  ambos: 'Cliente e Prestadora',
};

interface Conta {
  id: number; nome: string; segmento: string;
  tipo?: string;
  email?: string; telefone?: string; cidade?: string; uf?: string;
}

interface Props {
  conta: Conta;
  onClose: () => void;
  onEdit: () => void;
}

export function ContaViewModal({ conta, onClose, onEdit }: Props) {
  return (
    <ModalShell title="Detalhes da Conta" onClose={onClose}>
      <div className="space-y-4">
        <div className="flex items-center gap-3 pb-4 border-b border-gray-200 dark:border-gray-700">
          <div className="w-12 h-12 rounded bg-gradient-to-br from-[#0176d3] to-[#0d9dda] flex items-center justify-center text-white font-bold text-lg">
            {conta.nome.charAt(0).toUpperCase()}
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{conta.nome}</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">{conta.segmento || 'Sem segmento'}</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {conta.tipo && <InfoItem icon={<Building2 size={18} />} label="Tipo" value={TIPO_LABELS[conta.tipo] || conta.tipo} />}
          {conta.email && <InfoItem icon={<Mail size={18} />} label="Email" value={conta.email} />}
          {conta.telefone && <InfoItem icon={<Phone size={18} />} label="Telefone" value={conta.telefone} />}
          {(conta.cidade || conta.uf) && <InfoItem icon={<MapPin size={18} />} label="Localização" value={[conta.cidade, conta.uf].filter(Boolean).join(' - ')} />}
          {conta.segmento && <InfoItem icon={<Tag size={18} />} label="Segmento" value={conta.segmento} />}
        </div>
        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={onClose} className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">Fechar</button>
          <button type="button" onClick={onEdit} className="px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded">Editar</button>
        </div>
      </div>
    </ModalShell>
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
