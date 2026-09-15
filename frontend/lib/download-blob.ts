/** Dispara download de um blob no navegador (PDF, XML, etc.). */
export function downloadBlobFile(blob: Blob, filename: string): void {
  const nome = (filename || "arquivo").replace(/[/\\?%*:|"<>]/g, "_").trim() || "arquivo";
  // File + octet-stream: o Chrome usa o nome do arquivo, não o UUID do blob:.
  const arquivo = new File([blob], nome, { type: "application/octet-stream" });
  const url = URL.createObjectURL(arquivo);
  const a = document.createElement("a");
  a.href = url;
  a.download = nome;
  a.rel = "noopener";
  a.style.display = "none";
  document.body.appendChild(a);
  a.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window }));
  window.setTimeout(() => {
    a.remove();
    URL.revokeObjectURL(url);
  }, 60_000);
}

/** @deprecated Use downloadBlobFile */
export const downloadBlobAsFile = downloadBlobFile;
