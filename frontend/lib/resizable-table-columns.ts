/**
 * Redimensionamento de colunas em tabelas HTML — arrastar a borda do cabeçalho.
 * A largura da tabela segue a soma das colunas (não 100%), para a última
 * coluna não absorver espaço em branco nem ficar esmagada.
 * Persiste larguras no localStorage por página + índice da tabela.
 */

const MIN_COL_WIDTH = 56;
const STORAGE_PREFIX = 'lwk-table-cols-v2:';

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

function shouldSkipTable(table: HTMLTableElement): boolean {
  if (table.dataset.resizableColumns === 'off') return true;
  if (table.closest('[data-resizable-columns="off"]')) return true;
  if (table.closest('.fc')) return true;
  if (table.dataset.resizableEnhanced === 'true') return true;
  const ths = table.querySelectorAll('thead tr:first-child th');
  return ths.length < 2;
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

function readColWidth(col: HTMLElement): number {
  const parsed = Number.parseFloat(col.style.width);
  if (Number.isFinite(parsed) && parsed >= MIN_COL_WIDTH) return parsed;
  return Math.max(MIN_COL_WIDTH, Math.round(col.getBoundingClientRect().width) || MIN_COL_WIDTH);
}

function syncTableWidth(table: HTMLTableElement, cols: HTMLElement[]) {
  const total = cols.reduce((sum, col) => sum + readColWidth(col), 0);
  table.style.width = `${total}px`;
  table.style.minWidth = `${total}px`;
  table.style.maxWidth = 'none';
}

function measureDefaultWidths(table: HTMLTableElement, ths: HTMLTableCellElement[]): number[] {
  const prevWidth = table.style.width;
  const prevMin = table.style.minWidth;
  const prevLayout = table.style.tableLayout;
  table.style.tableLayout = 'auto';
  table.style.width = 'max-content';
  table.style.minWidth = '0';
  const widths = ths.map((th) =>
    Math.max(MIN_COL_WIDTH, Math.round(th.scrollWidth) || Math.round(th.getBoundingClientRect().width) || 120),
  );
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
  table.style.tableLayout = 'fixed';

  const cols = ensureColgroup(table, ths.length);
  const saved = loadWidths(storageKey, ths.length);

  ths.forEach((th, index) => {
    const width = (saved[index] || defaultWidths[index]);
    cols[index].style.width = `${Math.max(MIN_COL_WIDTH, width)}px`;
  });
  syncTableWidth(table, cols);

  ths.forEach((th, index) => {
    if (th.querySelector('.col-resize-handle')) return;

    th.classList.add('col-resize-th');
    const handle = document.createElement('div');
    handle.className = 'col-resize-handle';
    handle.setAttribute('role', 'separator');
    handle.setAttribute('aria-orientation', 'vertical');
    handle.setAttribute('aria-label', 'Redimensionar coluna');
    handle.title = 'Arrastar para redimensionar · duplo clique para restaurar';

    const persistWidths = () => {
      const widths = cols.map((col) => Math.round(readColWidth(col)));
      saveWidths(storageKey, widths);
      syncTableWidth(table, cols);
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
      const resetW = Math.max(MIN_COL_WIDTH, defaults[index] ?? 120);
      cols[index].style.width = `${resetW}px`;
      persistWidths();
    });

    handle.addEventListener('mousedown', (event) => {
      event.preventDefault();
      event.stopPropagation();

      const startX = event.clientX;
      const startWidth = readColWidth(cols[index]);

      const onMove = (e: MouseEvent) => {
        const next = Math.max(MIN_COL_WIDTH, startWidth + e.clientX - startX);
        cols[index].style.width = `${next}px`;
        syncTableWidth(table, cols);
      };

      const onUp = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        document.body.classList.remove('col-resize-active');
        persistWidths();
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
