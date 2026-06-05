/**
 * Redimensionamento de colunas em tabelas HTML — arrastar a borda do cabeçalho.
 * Persiste larguras no localStorage por página + índice da tabela.
 */

const MIN_COL_WIDTH = 56;
const STORAGE_PREFIX = 'lwk-table-cols:';

function loadWidths(key: string): number[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(`${STORAGE_PREFIX}${key}`);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((n) => typeof n === 'number' && n >= MIN_COL_WIDTH) : [];
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

function ensureColgroup(table: HTMLTableElement, count: number): HTMLColElement[] {
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

export function attachResizableTableColumns(table: HTMLTableElement, storageKey: string): void {
  if (shouldSkipTable(table)) return;

  const headerRow = table.querySelector('thead tr');
  if (!headerRow) return;

  const ths = Array.from(headerRow.querySelectorAll('th'));
  if (ths.length < 2) return;

  const defaultWidths = ths.map((th) =>
    Math.max(MIN_COL_WIDTH, Math.round(th.getBoundingClientRect().width) || 120),
  );
  table.dataset.colDefaultWidths = JSON.stringify(defaultWidths);

  table.dataset.resizableEnhanced = 'true';
  table.classList.add('table-cols-resizable');
  table.style.tableLayout = 'fixed';
  table.style.width = '100%';

  const cols = ensureColgroup(table, ths.length);
  const saved = loadWidths(storageKey);

  ths.forEach((th, index) => {
    const width = saved[index] ?? defaultWidths[index];
    cols[index].style.width = `${Math.max(MIN_COL_WIDTH, width)}px`;

    if (th.querySelector('.col-resize-handle')) return;

    th.classList.add('col-resize-th');
    const handle = document.createElement('div');
    handle.className = 'col-resize-handle';
    handle.setAttribute('role', 'separator');
    handle.setAttribute('aria-orientation', 'vertical');
    handle.setAttribute('aria-label', 'Redimensionar coluna');
    handle.title = 'Arrastar para redimensionar · duplo clique para restaurar';

    const persistWidths = () => {
      const widths = cols.map((col) => {
        const w = col.getBoundingClientRect().width;
        return Math.max(MIN_COL_WIDTH, Math.round(w));
      });
      saveWidths(storageKey, widths);
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
      const startWidth = cols[index].getBoundingClientRect().width || defaultWidths[index];

      const onMove = (e: MouseEvent) => {
        const next = Math.max(MIN_COL_WIDTH, startWidth + e.clientX - startX);
        cols[index].style.width = `${next}px`;
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
