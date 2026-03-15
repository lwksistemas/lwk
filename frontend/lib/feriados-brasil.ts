/**
 * Feriados nacionais do Brasil - para exibição no calendário (estilo Google Calendar)
 * Inclui feriados fixos e móveis (baseados na Páscoa)
 */

export interface FeriadoEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  allDay: boolean;
  backgroundColor: string;
  borderColor: string;
  display?: 'background' | 'auto' | 'block' | 'list-item';
  editable: boolean;
  extendedProps?: { tipo: 'feriado' };
}

/** Calcula a data da Páscoa (algoritmo de Meeus/Jones) */
function calcularPascoa(ano: number): Date {
  const a = ano % 19;
  const b = Math.floor(ano / 100);
  const c = ano % 100;
  const d = Math.floor(b / 4);
  const e = b % 4;
  const f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4);
  const k = c % 4;
  const l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const mes = Math.floor((h + l - 7 * m + 114) / 31);
  const dia = ((h + l - 7 * m + 114) % 31) + 1;
  return new Date(ano, mes - 1, dia);
}

/** Feriados fixos (dia/mês) */
const FERIADOS_FIXOS: Array<{ dia: number; mes: number; nome: string }> = [
  { dia: 1, mes: 1, nome: 'Ano Novo' },
  { dia: 21, mes: 4, nome: 'Tiradentes' },
  { dia: 1, mes: 5, nome: 'Dia do Trabalho' },
  { dia: 7, mes: 9, nome: 'Independência do Brasil' },
  { dia: 12, mes: 10, nome: 'Nossa Senhora Aparecida' },
  { dia: 2, mes: 11, nome: 'Finados' },
  { dia: 15, mes: 11, nome: 'Proclamação da República' },
  { dia: 25, mes: 12, nome: 'Natal' },
];

/** Gera eventos de feriados para um intervalo de datas */
export function obterFeriadosBrasil(start: Date, end: Date): FeriadoEvent[] {
  const eventos: FeriadoEvent[] = [];
  const anoInicio = start.getFullYear();
  const anoFim = end.getFullYear();

  const corBg = '#fef3c7'; // âmbar claro (estilo Google)
  const corBorder = '#d97706';

  for (let ano = anoInicio; ano <= anoFim; ano++) {
    // Feriados fixos
    for (const f of FERIADOS_FIXOS) {
      const data = new Date(ano, f.mes - 1, f.dia);
      if (data >= start && data < end) {
        const dataStr = `${ano}-${String(f.mes).padStart(2, '0')}-${String(f.dia).padStart(2, '0')}`;
        eventos.push({
          id: `feriado-${f.dia}-${f.mes}-${ano}`,
          title: `🎉 ${f.nome}`,
          start: dataStr,
          end: dataStr,
          allDay: true,
          backgroundColor: corBg,
          borderColor: corBorder,
          display: 'block',
          editable: false,
          extendedProps: { tipo: 'feriado' },
        });
      }
    }

    // Feriados móveis (baseados na Páscoa)
    const pascoa = calcularPascoa(ano);
    const addDays = (d: Date, n: number) => {
      const r = new Date(d);
      r.setDate(r.getDate() + n);
      return r;
    };

    const sextaSanta = addDays(pascoa, -2);
    const carnaval = addDays(pascoa, -47); // Terça de Carnaval
    const corpusChristi = addDays(pascoa, 60);

    const moveis = [
      { data: sextaSanta, nome: 'Sexta-feira Santa' },
      { data: carnaval, nome: 'Carnaval' },
      { data: corpusChristi, nome: 'Corpus Christi' },
    ];

    for (const m of moveis) {
      if (m.data >= start && m.data < end) {
        const y = m.data.getFullYear();
        const mo = String(m.data.getMonth() + 1).padStart(2, '0');
        const d = String(m.data.getDate()).padStart(2, '0');
        const dataStr = `${y}-${mo}-${d}`;
        eventos.push({
          id: `feriado-${m.nome.replace(/\s/g, '-')}-${ano}`,
          title: `🎉 ${m.nome}`,
          start: dataStr,
          end: dataStr,
          allDay: true,
          backgroundColor: corBg,
          borderColor: corBorder,
          display: 'block',
          editable: false,
          extendedProps: { tipo: 'feriado' },
        });
      }
    }
  }

  return eventos;
}
