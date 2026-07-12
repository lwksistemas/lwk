import { clinicaBelezaFetch } from "./fetch";
import {
  buildClinicaBelezaListUrl,
  parseClinicaBelezaListResponse,
  parseClinicaBelezaResponseBody,
} from "./pagination";

type QueryParams = Record<string, string | number | boolean | null | undefined>;

export async function cbGetList<T = unknown>(
  path: string,
  params?: QueryParams,
  loja?: { id?: number; slug?: string } | null,
): Promise<T[]> {
  const data = await cbGet(path, params, loja);
  return parseClinicaBelezaListResponse<T>(data);
}

export async function cbGet<T = unknown>(
  path: string,
  params?: QueryParams,
  loja?: { id?: number; slug?: string } | null,
): Promise<T> {
  const url = params ? buildClinicaBelezaListUrl(path, params) : path;
  const res = await clinicaBelezaFetch(url, {}, loja);
  const data = await parseClinicaBelezaResponseBody(res);
  if (!res.ok) throw data;
  return data as T;
}

export async function cbPost<T = unknown>(
  path: string,
  data: unknown,
  loja?: { id?: number; slug?: string } | null,
): Promise<T> {
  const res = await clinicaBelezaFetch(
    path,
    { method: "POST", body: JSON.stringify(data) },
    loja,
  );
  const body = await parseClinicaBelezaResponseBody(res);
  if (!res.ok) throw body;
  return body as T;
}

export async function cbPut<T = unknown>(
  path: string,
  data: unknown,
  loja?: { id?: number; slug?: string } | null,
): Promise<T> {
  const res = await clinicaBelezaFetch(
    path,
    { method: "PUT", body: JSON.stringify(data) },
    loja,
  );
  const body = await parseClinicaBelezaResponseBody(res);
  if (!res.ok) throw body;
  return body as T;
}

export async function cbPatch<T = unknown>(
  path: string,
  data: unknown,
  loja?: { id?: number; slug?: string } | null,
): Promise<T> {
  const res = await clinicaBelezaFetch(
    path,
    { method: "PATCH", body: JSON.stringify(data) },
    loja,
  );
  const body = await parseClinicaBelezaResponseBody(res);
  if (!res.ok) throw body;
  return body as T;
}

export async function cbDelete(path: string): Promise<void> {
  const res = await clinicaBelezaFetch(path, { method: "DELETE" });
  if (res.status === 204) return;
  const body = await parseClinicaBelezaResponseBody(res);
  if (!res.ok) throw body;
}
