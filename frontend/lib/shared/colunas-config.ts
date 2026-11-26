/** Definições genéricas de colunas configuráveis em listagens. */

export type ColunaDef = { key: string; label: string };

/** @deprecated Use ColunaDef. Mantido para compatibilidade com CRM. */
export type CrmColunaDef = ColunaDef;

export function colunasVisiveisFromConfig(
  keys: string[] | undefined | null,
  disponiveis: ColunaDef[],
  defaults: string[],
): ColunaDef[] {
  const labelMap = Object.fromEntries(disponiveis.map((c) => [c.key, c.label]));
  const resolved = keys && keys.length > 0 ? keys : defaults;
  return resolved.map((key) => ({ key, label: labelMap[key] || key }));
}
