#!/usr/bin/env node
/**
 * Gera PDFs dos manuais Meta Cloud API a partir dos HTML em output/.
 * Requer: npm install puppeteer (ou npx puppeteer)
 */
import { readFileSync, mkdirSync, existsSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');
const outDir = join(root, 'output');
const docsDir = join(root, '..', 'docs');

const jobs = [
  ['manual-whatsapp-meta-cloud-lwk.html', 'manual-whatsapp-meta-cloud-lwk.pdf'],
  ['manual-whatsapp-meta-cloud-php-mysql.html', 'manual-whatsapp-meta-cloud-php-mysql.pdf'],
];

async function main() {
  const puppeteer = await import('puppeteer');
  if (!existsSync(outDir)) mkdirSync(outDir, { recursive: true });
  if (!existsSync(docsDir)) mkdirSync(docsDir, { recursive: true });

  const browser = await puppeteer.default.launch({ headless: 'new', args: ['--no-sandbox'] });

  for (const [htmlName, pdfName] of jobs) {
    const htmlPath = join(outDir, htmlName);
    if (!existsSync(htmlPath)) {
      console.error(`HTML não encontrado: ${htmlPath}`);
      console.error('Execute primeiro: php gerar_manual_meta_lwk.php (ou gere o HTML manualmente)');
      process.exitCode = 1;
      continue;
    }
    const html = readFileSync(htmlPath, 'utf8');
    const page = await browser.newPage();
    await page.setContent(html, { waitUntil: 'networkidle0' });
    const pdfPath = join(docsDir, pdfName);
    await page.pdf({
      path: pdfPath,
      format: 'A4',
      printBackground: true,
      margin: { top: '14mm', right: '12mm', bottom: '14mm', left: '12mm' },
    });
    await page.close();
    console.log(`PDF: ${pdfPath}`);
  }

  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
