'use client';

import { useMemo, useState } from 'react';
import { ChevronLeft, ChevronRight, Printer, Search } from 'lucide-react';
import { TEAL } from '@/lib/clinica-geral-theme';
import { formatDateBR, toISODate } from '@/lib/clinica-geral-utils';

const ABAS = [
  { id: 'valor', label: 'Com Valor', itens: ['Peso', 'Altura', 'IMC', 'PA', 'FC', 'Temperatura'] },
  { id: 'fisico', label: 'Exame físico', itens: ['Geral', 'Cabeça', 'Pescoço', 'Tórax', 'Abdome', 'MMSS', 'MMII'] },
  { id: 'bio', label: 'Bioquímica', itens: ['Glicose', 'Ureia', 'Creatinina', 'TGO', 'TGP', 'Colesterol'] },
  { id: 'urina', label: 'Urina I', itens: ['Densidade', 'pH', 'Proteínas', 'Glicose', 'Leucócitos', 'Hemácias'] },
  { id: 'horm', label: 'Hormônios', itens: ['TSH', 'T4 livre', 'T3', 'Cortisol', 'Insulina'] },
  { id: 'hemo', label: 'Hemograma completo', itens: ['Hemácias', 'Hemoglobina', 'Hematócrito', 'Leucócitos', 'Plaquetas'] },
] as const;

export function ProntuarioExames() {
  const [aba, setAba] = useState<(typeof ABAS)[number]['id']>('valor');
  const [datas, setDatas] = useState<string[]>([]);
  const [busca, setBusca] = useState('');
  const atual = ABAS.find((a) => a.id === aba) || ABAS[0];
  const linhas = useMemo(
    () => atual.itens.filter((nome) => nome.toLowerCase().includes(busca.trim().toLowerCase())),
    [atual, busca],
  );

  return (
    <div className="min-w-0 flex-1">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => setDatas((d) => (d.includes(toISODate(new Date())) ? d : [toISODate(new Date()), ...d]))}
          className="rounded-md px-3 py-1.5 text-sm font-medium text-white"
          style={{ backgroundColor: TEAL }}
        >
          Nova Data
        </button>
        <select className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700">
          <option>Prontuário: Clínica</option>
        </select>
        <button type="button" className="rounded-md border border-slate-200 p-1.5 text-slate-500" title="Imprimir" onClick={() => window.print()}>
          <Printer className="h-4 w-4" />
        </button>
      </div>

      <div className="mb-3 flex flex-wrap items-center gap-2">
        {ABAS.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => setAba(item.id)}
            className={`rounded-md px-3 py-1.5 text-sm ${aba === item.id ? 'bg-slate-200 font-medium text-slate-800' : 'text-slate-500 hover:bg-slate-100'}`}
          >
            {item.label}
          </button>
        ))}
        <span className="ml-auto flex items-center gap-1 text-slate-400">
          <ChevronLeft className="h-4 w-4" />
          <ChevronRight className="h-4 w-4" />
        </span>
        <label className="flex items-center gap-2 rounded-md border border-slate-200 px-2 py-1 text-sm">
          <Search className="h-3.5 w-3.5 text-slate-400" />
          <input
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="O que você procura?"
            className="w-40 bg-transparent outline-none placeholder:text-slate-400"
          />
        </label>
      </div>

      <div className="overflow-auto rounded-md border border-slate-200">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-500">
            <tr>
              <th className="px-3 py-2 font-medium">Nome</th>
              {datas.map((data) => (
                <th key={data} className="px-3 py-2 font-medium">
                  {formatDateBR(data)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {linhas.map((nome) => (
              <tr key={nome} className="border-t border-slate-100">
                <td className="px-3 py-2 text-slate-700">{nome}</td>
                {datas.map((data) => (
                  <td key={`${nome}-${data}`} className="px-3 py-2 text-slate-400">
                    —
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
