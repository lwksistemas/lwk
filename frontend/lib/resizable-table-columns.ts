/**
 * Redimensionamento de colunas em tabelas HTML — arrastar a borda do cabeçalho.
 *
 * Larguras persistidas são as que o usuário escolheu. Se a soma for menor que
 * o container, o espaço extra vai para a primeira coluna (a tabela preenche a
 * tela e a última coluna não fica esticada).
 */

const MIN_COL_WIDTH = 72;
const HEADER_PAD = 32;
const STORAGE_PREFIX = 'lwk-table-cols-v3:';

export function applyIntendedColumnWidths(
  table: HTMLTableElement,
  cols: HTMLElement[],
  intended: number[],
): void {
  const total = intended.reduce((sum, w) => sum + Math.max(MIN_COL_WIDTH, w), 0);
  const available = table.parentElement?.clientWidth ?? 0;
  const extra = Math.max(0, available - total);

  table.style.tableLayout = 'fixed';
  table.style.minWidth = `${total}px`;
  table.style.maxWidth = 'none';
  table.style.width = extra > 0 ? '100%' : `${total}px`;

  cols.forEach((col, i) => {
    const base = Math.max(MIN_COL_WIDTH, intended[i] ?? MIN_COL_WIDTH);
    col.style.width = `${i === 0 ? base + extra : base}px`;
  });
  table.dataset.colIntendedWidths = JSON.stringify(intended.map((w) => Math.max(MIN_COL_WIDTH, w)));
}

function loadWidths(key: string, count: number): number[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(`${STORAGE_PREFIX}${key}`);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed) || parsed.length !== count) return [];
    return parsed.map((n) => (typeof n === 'number' && n >= MIN_COL_WIDTH ? n : 0));
  } catch {
    return [];
  }
}

function saveWidths(key: string, widths: number[]) {
  try {
    localStorage.setItem(`${STORAGE_PREFIX}${key}`, JSON.stringify(widths));
  } catch {
    /* quota / privado */
  }
}

const resizeObservers = new WeakMap<HTMLTableElement, ResizeObserver>();

function readIntended(table: HTMLTableElement, count: number): number[] {
  try {
    const parsed = JSON.parse(table.dataset.colIntendedWidths || '[]');
    if (Array.isArray(parsed) && parsed.length === count) {
      return parsed.map((n) =>
        typeof n === 'number' && n >= MIN_COL_WIDTH ? n : MIN_COL_WIDTH,
      );
    }
  } catch {
    /* ignora */
  }
  return [];
}

function resetEnhancement(table: HTMLTableElement) {
  resizeObservers.get(table)?.disconnect();
  resizeObservers.delete(table);
  delete table.dataset.colResizeObserver;
  table.dataset.resizableEnhanced = 'false';
  table.querySelectorAll('.col-resize-handle').forEach((h) => h.remove());
}

function shouldSkipTable(table: HTMLTableElement): boolean {
  if (table.dataset.resizableColumns === 'off') return true;
  if (table.closest('[data-resizable-columns="off"]')) return true;
  if (table.closest('.fc')) return true;
  const ths = table.querySelectorAll('thead tr:first-child th');
  if (ths.length < 2) return true;
  if (table.dataset.resizableEnhanced === 'true') {
    const cols = table.querySelectorAll('colgroup col');
    if (cols.length === ths.length) return true;
    resetEnhancement(table);
  }
  return false;
}

function ensureColgroup(table: HTMLTableElement, count: number): HTMLElement[] {
  let colgroup = table.querySelector('colgroup');
  if (!colgroup) {
    colgroup = document.createElement('colgroup');
    table.insertBefore(colgroup, table.firstChild);
  }
  while (colgroup.children.length < count) {
    colgroup.appendChild(document.createElement('col'));
  }
  while (colgroup.children.length > count) {
    colgroup.removeChild(colgroup.lastChild!);
  }
  return Array.from(colgroup.querySelectorAll('col'));
}

function measureDefaultWidths(table: HTMLTableElement, ths: HTMLTableCellElement[]): number[] {
  const prevWidth = table.style.width;
  const prevMin = table.style.minWidth;
  const prevLayout = table.style.tableLayout;
  table.style.tableLayout = 'auto';
  table.style.width = 'max-content';
  table.style.minWidth = '0';
  const widths = ths.map((th) => {
    const rect = Math.round(th.getBoundingClientRect().width);
    const scroll = Math.round(th.scrollWidth);
    return Math.max(MIN_COL_WIDTH, rect, scroll + HEADER_PAD);
  });
  table.style.tableLayout = prevLayout;
  table.style.width = prevWidth;
  table.style.minWidth = prevMin;
  return widths;
}

export function attachResizableTableColumns(table: HTMLTableElement, storageKey: string): void {
  if (shouldSkipTable(table)) return;

  const headerRow = table.querySelector('thead tr');
  if (!headerRow) return;

  const ths = Array.from(headerRow.querySelectorAll('th'));
  if (ths.length < 2) return;

  const defaultWidths = measureDefaultWidths(table, ths);
  table.dataset.colDefaultWidths = JSON.stringify(defaultWidths);

  table.dataset.resizableEnhanced = 'true';
  table.classList.add('table-cols-resizable');

  const cols = ensureColgroup(table, ths.length);
  const saved = loadWidths(storageKey, ths.length);
  const intended = ths.map((_, index) => saved[index] || defaultWidths[index]);
  applyIntendedColumnWidths(table, cols, intended);

  if (!table.dataset.colResizeObserver) {
    table.dataset.colResizeObserver = '1';
    const parent = table.parentElement;
    if (parent && typeof ResizeObserver !== 'undefined') {
      const ro = new ResizeObserver(() => {
        const liveCols = Array.from(table.querySelectorAll('colgroup col')) as HTMLElement[];
        const current = readIntended(table, liveCols.length);
        if (current.length) applyIntendedColumnWidths(table, liveCols, current);
      });
      ro.observe(parent);
      resizeObservers.set(table, ro);
    }
  }

  ths.forEach((th, index) => {
    if (th.querySelector('.col-resize-handle')) return;

    th.classList.add('col-resize-th');
    const handle = document.createElement('div');
    handle.className = 'col-resize-handle';
    handle.setAttribute('role', 'separator');
    handle.setAttribute('aria-orientation', 'vertical');
    handle.setAttribute('aria-label', 'Redimensionar coluna');
    handle.title = 'Arrastar para redimensionar · duplo clique para restaurar';

    const persistWidths = (next: number[]) => {
      saveWidths(storageKey, next);
      applyIntendedColumnWidths(table, cols, next);
    };

    handle.addEventListener('dblclick', (event) => {
      event.preventDefault();
      event.stopPropagation();
      let defaults: number[] = defaultWidths;
      try {
        const parsed = JSON.parse(table.dataset.colDefaultWidths || '[]');
        if (Array.isArray(parsed) && parsed[index] != null) {
          defaults = parsed;
        }
      } catch {
        /* mantém defaultWidths */
      }
      const current = readIntended(table, cols.length);
      const next = (current.length ? current : intended).slice();
      next[index] = Math.max(MIN_COL_WIDTH, defaults[index] ?? 120);
      persistWidths(next);
    });

    handle.addEventListener('mousedown', (event) => {
      event.preventDefault();
      event.stopPropagation();

      const startX = event.clientX;
      const stored = readIntended(table, cols.length);
      const startIntended = (stored.length ? stored : intended).slice();
      const startWidth =
        Math.round(cols[index].getBoundingClientRect().width) || startIntended[index] || MIN_COL_WIDTH;

      const onMove = (e: MouseEvent) => {
        const next = startIntended.slice();
        next[index] = Math.max(MIN_COL_WIDTH, startWidth + e.clientX - startX);
        applyIntendedColumnWidths(table, cols, next);
      };

      const onUp = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        document.body.classList.remove('col-resize-active');
        const next = readIntended(table, cols.length);
        if (next.length) saveWidths(storageKey, next);
      };

      document.body.classList.add('col-resize-active');
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });

    th.appendChild(handle);
  });
}

export function enhanceResizableTables(pathname: string): void {
  if (typeof document === 'undefined') return;

  const tables = document.querySelectorAll('table');
  tables.forEach((node, index) => {
    const table = node as HTMLTableElement;
    const key = `${pathname}#${index}`;
    attachResizableTableColumns(table, key);
  });
}

export function resyncResizableTables(): void {
  if (typeof document === 'undefined') return;
  document.querySelectorAll('table.table-cols-resizable').forEach((node) => {
    const table = node as HTMLTableElement;
    const cols = Array.from(table.querySelectorAll('colgroup col')) as HTMLElement[];
    const intended = readIntended(table, cols.length);
    if (intended.length && cols.length === intended.length) {
      applyIntendedColumnWidths(table, cols, intended);
    }
  });
}
