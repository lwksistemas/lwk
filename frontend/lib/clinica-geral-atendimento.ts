import type { Consulta, Evolucao, ExameFisicoFicha, FichaAtendimento, ItemFicha, Prescricao } from '@/lib/clinica-geral-types';

export const ABAS_ATENDIMENTO = [
  { id: 'HMA', label: 'HMA', titulo: 'História e motivo do atendimento' },
  { id: 'TrA', label: 'TrA', titulo: 'Tratamentos em andamento' },
  { id: 'AP', label: 'AP', titulo: 'Antecedentes pessoais' },
  { id: 'EF', label: 'EF', titulo: 'Exame físico' },
  { id: 'EM', label: 'EM', titulo: 'Escalas médicas' },
  { id: 'TA', label: 'TA', titulo: 'Terapêutica adotada' },
  { id: 'DIAG', label: 'DIAG', titulo: 'Diagnóstico' },
  { id: 'Lx', label: 'Lx', titulo: 'Tabela de acompanhamento' },
  { id: 'Rx', label: 'Rx', titulo: 'Receituário' },
  { id: 'ENC', label: 'ENC', titulo: 'Encaminhamento' },
  { id: 'SP', label: 'SP', titulo: 'Sumário do prontuário' },
  { id: 'AM', label: 'AM', titulo: 'Atestado médico' },
] as const;

export type AbaAtendimento = (typeof ABAS_ATENDIMENTO)[number]['id'];

export const QUEIXAS = [
  'Diabetes Mellitus',
  'Cefaléia',
  'Hipertensão arterial',
  'Dor abdominal',
  'Tosse',
  'Febre',
  'Ansiedade',
  'Fadiga',
  'Dor lombar',
  'Dispneia',
];

export const ANTECEDENTES_CLINICOS = [
  'Artrites Reumatóides',
  'Depressão',
  'Diabetes Mellitus',
  'Hipertensão arterial',
  'Insuficiência renal crônica',
  'Asma',
  'Dislipidemia',
  'Hipotireoidismo',
  'Obesidade',
  'Tabagismo',
];

export const ANTECEDENTES_CIRURGICOS = [
  'Amigdalectomia',
  'Apendicectomia',
  'Cesárea',
  'Colecistectomia',
  'Histerectomia',
  'Herniorrafia',
];

export const MEDICAMENTOS = [
  'Losartana',
  'Metformina',
  'Omeprazol',
  'Sinvastatina',
  'AAS',
  'Enalapril',
  'Anlodipino',
  'Levotiroxina',
];

export const ESCALAS_MEDICAS = [
  'AIVD',
  'AVD',
  'Caprini',
  'CHA2DS2-VASc',
  'Child Pugh',
  'DAS28',
  'Framingham',
  'GDS',
  'HAS-BLED',
  'Kupperman e Blatt',
  'LEE',
  'LEE-VASC',
  'MEEM',
  'Wagner',
];

export const DURACOES = ['Até 24h', '1 a 3 dias', '1 semana', '1 mês', 'Mais de 1 mês', 'Crônico'];
export const STATUS_ANTECEDENTE = ['Ativo', 'Resolvido', 'Em investigação'];

export function emptyExame(): ExameFisicoFicha {
  return {
    peso: '',
    altura: '',
    sc: '',
    temperatura: '',
    imc: '',
    circ_abdominal: '',
    pas_sentado: '',
    pad_sentado: '',
    pas_deitado: '',
    pad_deitado: '',
    aspecto_geral: '',
    mucosas: '',
    olhos_face: '',
    pescoco: '',
    cardiorespiratorio: '',
    pele: '',
    abdome_superior: '',
    abdome_inferior: '',
    osteomuscular: '',
    membros: '',
    neurologico: '',
    outras: '',
  };
}

export function emptyFicha(): FichaAtendimento {
  return {
    queixas: [],
    historia_doenca: '',
    tratamentos: [],
    antecedentes_clinicos: [],
    antecedentes_cirurgicos: [],
    exame: emptyExame(),
    diagnostico: '',
    terapeutica: '',
    encaminhamento: '',
    laudos: '',
    sumario: '',
    atestado: '',
  };
}

export function mergeFicha(raw?: Partial<FichaAtendimento> | null): FichaAtendimento {
  const base = emptyFicha();
  if (!raw || typeof raw !== 'object') return base;
  return {
    ...base,
    ...raw,
    queixas: raw.queixas || [],
    tratamentos: raw.tratamentos || [],
    antecedentes_clinicos: raw.antecedentes_clinicos || [],
    antecedentes_cirurgicos: raw.antecedentes_cirurgicos || [],
    exame: { ...base.exame, ...(raw.exame || {}) },
  };
}

export function calcIMC(peso: string, alturaCm: string): string {
  const p = Number(String(peso).replace(',', '.'));
  const a = Number(String(alturaCm).replace(',', '.')) / 100;
  if (!Number.isFinite(p) || !Number.isFinite(a) || p <= 0 || a <= 0) return '';
  return (p / (a * a)).toFixed(1);
}

export function calcSC(peso: string, alturaCm: string): string {
  const p = Number(String(peso).replace(',', '.'));
  const a = Number(String(alturaCm).replace(',', '.'));
  if (!Number.isFinite(p) || !Number.isFinite(a) || p <= 0 || a <= 0) return '';
  return Math.sqrt((a * p) / 3600).toFixed(2);
}

export function fichaParaSoap(ficha: FichaAtendimento): {
  subjetivo: string;
  objetivo: string;
  avaliacao: string;
  plano: string;
} {
  const queixas = ficha.queixas.map((q) => [q.nome, q.duracao, q.nota].filter(Boolean).join(' — ')).join('\n');
  const exame = ficha.exame;
  const vitais = [
    exame.peso && `Peso ${exame.peso} kg`,
    exame.altura && `Altura ${exame.altura} cm`,
    exame.imc && `IMC ${exame.imc}`,
    exame.temperatura && `Temp ${exame.temperatura} °C`,
    (exame.pas_sentado || exame.pad_sentado) && `PA sentado ${exame.pas_sentado}/${exame.pad_sentado}`,
  ]
    .filter(Boolean)
    .join(' · ');
  const tratamentos = ficha.tratamentos.map((t) => t.nome).join(', ');
  return {
    subjetivo: [queixas, ficha.historia_doenca].filter(Boolean).join('\n\n'),
    objetivo: [vitais, exame.aspecto_geral, exame.outras].filter(Boolean).join('\n'),
    avaliacao: ficha.diagnostico,
    plano: [tratamentos, ficha.terapeutica].filter(Boolean).join('\n'),
  };
}

export function toggleItem(lista: ItemFicha[], nome: string): ItemFicha[] {
  if (lista.some((i) => i.nome === nome)) return lista.filter((i) => i.nome !== nome);
  return [...lista, { nome, status: 'Ativo', duracao: 'Até 24h', nota: '' }];
}

export function formatTimer(segundos: number): string {
  const m = Math.floor(Math.max(0, segundos) / 60);
  const s = Math.max(0, segundos) % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export function resumoAbaFicha(aba: AbaAtendimento, ficha: FichaAtendimento): string[] {
  const f = mergeFicha(ficha);
  if (aba === 'HMA') {
    return [...f.queixas.map((q) => [q.nome, q.duracao].filter(Boolean).join(' — ')), f.historia_doenca].filter(Boolean);
  }
  if (aba === 'TrA') return f.tratamentos.map((t) => t.nome).filter(Boolean);
  if (aba === 'AP') {
    return [
      ...f.antecedentes_clinicos.map((i) => i.nome),
      ...f.antecedentes_cirurgicos.map((i) => `${i.nome} (cirúrgico)`),
    ].filter(Boolean);
  }
  if (aba === 'EF') {
    const e = f.exame;
    return [
      e.peso && `Peso ${e.peso} kg`,
      e.altura && `Altura ${e.altura} cm`,
      e.imc && `IMC ${e.imc}`,
      e.aspecto_geral,
    ].filter((v): v is string => Boolean(v));
  }
  if (aba === 'TA') return [f.terapeutica].filter(Boolean);
  if (aba === 'DIAG') return [f.diagnostico].filter(Boolean);
  if (aba === 'ENC') return [f.encaminhamento].filter(Boolean);
  if (aba === 'SP') return [f.sumario].filter(Boolean);
  if (aba === 'AM') return [f.atestado].filter(Boolean);
  return [];
}

export function isAnexoImagem(nome: string, url = ''): boolean {
  return /\.(jpe?g|png|gif|webp|bmp|heic)$/i.test(nome || url.split('?')[0]);
}

const ESCALAS_OCULTAS_KEY = 'clinica-geral-escalas-ocultas';

export function lerEscalasOcultas(): string[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(ESCALAS_OCULTAS_KEY);
    const lista = raw ? (JSON.parse(raw) as unknown) : [];
    return Array.isArray(lista) ? lista.filter((x) => typeof x === 'string') : [];
  } catch {
    return [];
  }
}

export function gravarEscalasOcultas(nomes: string[]): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(ESCALAS_OCULTAS_KEY, JSON.stringify(nomes));
}

export type LinhaResumoClinico = {
  texto: string;
  data: string;
  hora?: string;
};

function dataHoraConsulta(consultaId: number, consultas: Consulta[], fallback?: string): { data: string; hora?: string } {
  const c = consultas.find((x) => x.id === consultaId);
  return { data: c?.data || fallback?.slice(0, 10) || '', hora: c?.hora };
}

export function coletarDiagnosticos(evolucoes: Evolucao[], consultas: Consulta[]): LinhaResumoClinico[] {
  const rows: LinhaResumoClinico[] = [];
  const seen = new Set<string>();
  for (const e of evolucoes) {
    const { data, hora } = dataHoraConsulta(e.consulta, consultas, e.updated_at);
    const ficha = mergeFicha(e.ficha);
    const atual = (ficha.diagnostico || e.avaliacao || '').trim();
    if (atual) {
      const key = atual.toLowerCase();
      if (!seen.has(key)) {
        seen.add(key);
        rows.push({ texto: atual, data, hora });
      }
    }
    for (const a of ficha.antecedentes_clinicos) {
      const texto = `${a.nome} (Diagnóstico antigo)`;
      const key = texto.toLowerCase();
      if (seen.has(key)) continue;
      seen.add(key);
      rows.push({ texto, data, hora });
    }
  }
  return rows;
}

export function coletarCirurgias(evolucoes: Evolucao[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const e of evolucoes) {
    for (const i of mergeFicha(e.ficha).antecedentes_cirurgicos) {
      if (seen.has(i.nome)) continue;
      seen.add(i.nome);
      out.push(i.nome);
    }
  }
  return out;
}

export function coletarTratamentos(evolucoes: Evolucao[], prescricoes: Prescricao[]): string[] {
  const textos = [
    ...evolucoes.flatMap((e) => {
      const ficha = mergeFicha(e.ficha);
      return [...ficha.tratamentos.map((t) => t.nome), e.plano, ficha.terapeutica];
    }),
    ...prescricoes.flatMap((p) => p.itens.map((i) => i.medicamento)),
  ];
  const seen = new Set<string>();
  const out: string[] = [];
  for (const raw of textos) {
    const texto = (raw || '').trim();
    if (!texto) continue;
    const key = texto.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(texto);
  }
  return out;
}
