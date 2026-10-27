import { describe, expect, it } from 'vitest';
import { textoParaEditor } from './crm-proposta-template-formatacao';

describe('editor do template', () => {
  it('tira o script e mantém a marca da segunda folha', () => {
    const html = textoParaEditor(
      '<p data-align="center">Investimento [[folha:2]]</p><script>alert(1)</script>',
    );
    expect(html).not.toContain('<script');
    expect(html).not.toContain('alert(1)');
    expect(html).toContain('[[folha:2]]');
    expect(html).toContain('data-align="center"');
  });
});
