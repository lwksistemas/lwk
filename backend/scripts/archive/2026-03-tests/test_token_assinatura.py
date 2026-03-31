#!/usr/bin/env python
"""
Script de teste para verificar geração e busca de tokens de assinatura digital.
"""
from urllib.parse import quote, unquote

def test_token_url_encoding():
    """Testa URL encoding de tokens com caracteres especiais"""
    print("=" * 80)
    print("TESTE: URL Encoding de Tokens Django")
    print("=" * 80)
    
    # Simular token Django (formato: payload:timestamp:signature)
    token_exemplo = "eyJkb2NfdHlwZSI6InByb3Bvc3RhIiwiZG9jX2lkIjoxMiwidGlwbyI6ImNsaWVudGUiLCJsb2phX2lkIjoxMzAsImV4cCI6MTc3NDUwOTI4M30:1w37ad:zsNEP-tV6kjH2988kMFST8OaPJ2rDinTsHMZSx729vw"
    
    print(f"\n📝 Token original:")
    print(f"   {token_exemplo}")
    print(f"   Tamanho: {len(token_exemplo)} caracteres")
    print(f"   Contém ':': {'Sim' if ':' in token_exemplo else 'Não'}")
    print(f"   Quantidade de ':': {token_exemplo.count(':')}")
    
    # Testar URL encoding
    token_encoded = quote(token_exemplo, safe='')
    print(f"\n📦 Token URL encoded:")
    print(f"   {token_encoded}")
    print(f"   Tamanho: {len(token_encoded)} caracteres")
    print(f"   ':' virou '%3A': {'Sim' if '%3A' in token_encoded else 'Não'}")
    
    # Testar URL decoding
    token_decoded = unquote(token_encoded)
    print(f"\n� Token URL decoded:")
    print(f"   {token_decoded}")
    print(f"   Igual ao original: {'✅ Sim' if token_decoded == token_exemplo else '❌ Não'}")
    
    # Testar se unquote em token não-encoded não muda nada
    token_decoded_direto = unquote(token_exemplo)
    print(f"\n🔄 Unquote em token não-encoded:")
    print(f"   Mudou algo: {'❌ Sim' if token_decoded_direto != token_exemplo else '✅ Não (esperado)'}")
    
    # Simular busca flexível
    print(f"\n� Simulação de busca flexível:")
    print(f"   1. Buscar token direto: {token_exemplo[:30]}...")
    print(f"   2. Se não encontrar, fazer unquote: {unquote(token_exemplo)[:30]}...")
    print(f"   3. Tokens são iguais: {'Sim (busca 1 funciona)' if token_exemplo == unquote(token_exemplo) else 'Não (busca 2 necessária)'}")
    
    return token_exemplo, token_encoded

if __name__ == '__main__':
    print("\n🧪 TESTE DE URL ENCODING PARA TOKENS DE ASSINATURA\n")
    
    token_original, token_encoded = test_token_url_encoding()
    
    print("\n" + "=" * 80)
    print("CONCLUSÃO")
    print("=" * 80)
    print("\n✅ O token Django contém ':' que precisa ser tratado em URLs")
    print("✅ URL encoding transforma ':' em '%3A'")
    print("✅ URL decoding restaura o token original")
    print("✅ Busca flexível (direto + unquote) garante compatibilidade")
    print("\n" + "=" * 80 + "\n")

