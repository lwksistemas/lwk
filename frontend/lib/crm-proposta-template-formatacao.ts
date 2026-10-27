import { familiaCss } from '@/lib/crm-proposta-template-legenda';

export type Alinhamento = 'left' | 'center' | 'right' | 'justify';

function escaparHtml(texto: string): string {
  return texto
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function htmlSemScript(html: string): string {
  return html
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '')
    .replace(/<iframe\b[^>]*>[\s\S]*?<\/iframe>/gi, '')
    .replace(/\son[a-z]+\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)/gi, '')
    .replace(/javascript\s*:/gi, '');
}

export function textoParaEditor(texto: string): string {
  const bruto = (texto || '').replace(/\r\n/g, '\n');
  if (!bruto.trim()) return '<p><br></p>';
  if (/<(p|div|span)\b/i.test(bruto)) return htmlSemScript(bruto);
  return bruto
    .split('\n')
    .map((linha) => `<p>${linha ? escaparHtml(linha) : '<br>'}</p>`)
    .join('');
}

function alinhamentoDoBloco(bloco: HTMLElement): Alinhamento {
  const valor = (bloco.dataset.align || bloco.style.textAlign || 'left').toLowerCase();
  if (valor === 'center' || valor === 'right' || valor === 'justify') return valor;
  return 'left';
}

function blocoFormatado(bloco: HTMLElement): boolean {
  if (alinhamentoDoBloco(bloco) !== 'left') return true;
  return Boolean(bloco.querySelector('span[data-font], span[data-size], span[data-bold]'));
}

function serializarInline(raiz: HTMLElement): string {
  let html = '';
  const visitar = (no: Node, fonte?: string, tamanho?: string, negrito?: boolean) => {
    if (no.nodeType === Node.TEXT_NODE) {
      const texto = (no.textContent || '').replace(/\u00a0/g, ' ');
      if (!texto) return;
      if (fonte || tamanho || negrito) {
        const attrs = `${fonte ? ` data-font="${fonte}"` : ''}${tamanho ? ` data-size="${tamanho}"` : ''}${negrito ? ' data-bold="1"' : ''}`;
        html += `<span${attrs}>${escaparHtml(texto)}</span>`;
      } else {
        html += escaparHtml(texto);
      }
      return;
    }
    if (!(no instanceof HTMLElement)) return;
    if (no.tagName === 'BR') {
      html += '<br>';
      return;
    }
    const proximaFonte = no.dataset.font || fonte;
    const proximoTamanho = no.dataset.size || tamanho;
    const proximoNegrito = no.dataset.bold === '1' ? true : no.dataset.bold === '0' ? false : negrito;
    for (const filho of no.childNodes) visitar(filho, proximaFonte, proximoTamanho, proximoNegrito);
  };
  for (const filho of raiz.childNodes) visitar(filho);
  return html;
}

function blocosDoEditor(raiz: HTMLElement): HTMLElement[] {
  const blocos: HTMLElement[] = [];
  for (const no of raiz.childNodes) {
    if (no instanceof HTMLElement && (no.tagName === 'P' || no.tagName === 'DIV')) {
      blocos.push(no);
      continue;
    }
    if (no.nodeType === Node.TEXT_NODE && no.textContent?.replace(/\u00a0/g, ' ').trim()) {
      const paragrafo = document.createElement('p');
      paragrafo.textContent = no.textContent.replace(/\u00a0/g, ' ');
      blocos.push(paragrafo);
    }
  }
  return blocos;
}

export function editorParaTexto(raiz: HTMLElement): string {
  const blocos = blocosDoEditor(raiz);
  if (blocos.length === 0) {
    return (raiz.innerText || '').replace(/\u00a0/g, ' ').trim();
  }
  while (blocos.length > 0 && !(blocos[blocos.length - 1].textContent || '').replace(/\u00a0/g, ' ').trim()) {
    blocos.pop();
  }
  if (blocos.length === 0) return '';
  if (!blocos.some(blocoFormatado)) {
    return blocos.map((bloco) => (bloco.textContent || '').replace(/\u00a0/g, ' ')).join('\n');
  }
  return blocos
    .map((bloco) => {
      const align = alinhamentoDoBloco(bloco);
      const attr = align === 'left' ? '' : ` data-align="${align}"`;
      const interno = serializarInline(bloco);
      return `<p${attr}>${interno || '<br>'}</p>`;
    })
    .join('');
}

function textosNoIntervalo(editor: HTMLElement, range: Range): Text[] {
  const raiz = range.commonAncestorContainer;
  const base = raiz.nodeType === Node.ELEMENT_NODE ? (raiz as Element) : raiz.parentElement;
  if (!base || !editor.contains(base)) return [];
  const walker = document.createTreeWalker(base, NodeFilter.SHOW_TEXT);
  const nos: Text[] = [];
  let no = walker.nextNode();
  while (no) {
    if (no.textContent && range.intersectsNode(no)) nos.push(no as Text);
    no = walker.nextNode();
  }
  return nos;
}

function marcarNegrito(span: HTMLElement, negrito: boolean) {
  if (negrito) {
    span.dataset.bold = '1';
    span.style.fontWeight = '700';
    return;
  }
  span.dataset.bold = '0';
  span.style.fontWeight = '400';
}

function spanSemFormato(span: HTMLElement) {
  return !span.dataset.font && !span.dataset.size && span.dataset.bold !== '1';
}

function desembrulhar(span: HTMLElement) {
  const pai = span.parentNode;
  if (!pai) return;
  while (span.firstChild) pai.insertBefore(span.firstChild, span);
  pai.removeChild(span);
}

function envolverTrecho(no: Text, inicio: number, fim: number, patch: { tipo?: string; tamanho?: number; negrito?: boolean }) {
  let alvo = no;
  if (fim < no.length) no.splitText(fim);
  if (inicio > 0) alvo = no.splitText(inicio);
  const pai = alvo.parentElement;
  if (pai?.tagName === 'SPAN' && pai.childNodes.length === 1 && pai.textContent === alvo.data) {
    if (patch.tipo) {
      pai.dataset.font = patch.tipo;
      pai.style.fontFamily = familiaCss(patch.tipo);
    }
    if (patch.tamanho) {
      pai.dataset.size = String(patch.tamanho);
      pai.style.fontSize = `${patch.tamanho}pt`;
    }
    if (patch.negrito !== undefined) marcarNegrito(pai, patch.negrito);
    if (spanSemFormato(pai) && !pai.parentElement?.closest('span[data-bold="1"]')) desembrulhar(pai);
    return;
  }
  const ancestral = pai?.closest('span[data-font], span[data-size], span[data-bold]');
  const span = document.createElement('span');
  const tipo = patch.tipo || ancestral?.dataset.font;
  const tamanho = patch.tamanho ? String(patch.tamanho) : ancestral?.dataset.size;
  const negrito = patch.negrito ?? ancestral?.dataset.bold === '1';
  if (tipo) {
    span.dataset.font = tipo;
    span.style.fontFamily = familiaCss(tipo);
  }
  if (tamanho) {
    span.dataset.size = tamanho;
    span.style.fontSize = `${tamanho}pt`;
  }
  if (negrito || patch.negrito === false) marcarNegrito(span, Boolean(negrito));
  if (spanSemFormato(span)) return;
  alvo.parentNode?.insertBefore(span, alvo);
  span.appendChild(alvo);
}

export function aplicarFonte(
  editor: HTMLElement,
  range: Range,
  patch: { tipo?: string; tamanho?: number },
): boolean {
  if (range.collapsed || !editor.contains(range.commonAncestorContainer)) return false;
  const nos = textosNoIntervalo(editor, range);
  if (nos.length === 0) return false;
  for (let indice = nos.length - 1; indice >= 0; indice -= 1) {
    const no = nos[indice];
    const inicio = no === range.startContainer ? range.startOffset : 0;
    const fim = no === range.endContainer ? range.endOffset : no.length;
    if (fim <= inicio) continue;
    envolverTrecho(no, inicio, fim, patch);
  }
  return true;
}

export function aplicarNegrito(editor: HTMLElement, range: Range): boolean {
  if (range.collapsed || !editor.contains(range.commonAncestorContainer)) return false;
  const nos = textosNoIntervalo(editor, range);
  if (nos.length === 0) return false;
  const ligar = nos.some((no) => no.parentElement?.closest('span[data-bold="1"]') == null);
  for (let indice = nos.length - 1; indice >= 0; indice -= 1) {
    const no = nos[indice];
    const inicio = no === range.startContainer ? range.startOffset : 0;
    const fim = no === range.endContainer ? range.endOffset : no.length;
    if (fim <= inicio) continue;
    envolverTrecho(no, inicio, fim, { negrito: ligar });
  }
  return true;
}

export function aplicarAlinhamento(editor: HTMLElement, range: Range, alinhamento: Alinhamento): boolean {
  if (range.collapsed || !editor.contains(range.commonAncestorContainer)) return false;
  const blocos = new Set<HTMLElement>();
  for (const no of textosNoIntervalo(editor, range)) {
    const bloco = no.parentElement?.closest('p, div');
    if (bloco instanceof HTMLElement && bloco !== editor && editor.contains(bloco)) blocos.add(bloco);
  }
  if (blocos.size === 0) return false;
  for (const bloco of blocos) {
    bloco.dataset.align = alinhamento;
    bloco.style.textAlign = alinhamento;
  }
  return true;
}
