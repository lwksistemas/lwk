#!/usr/bin/env python
"""
Script para instalar dependências necessárias no Heroku
"""
import subprocess
import sys

def install_package(package):
    """Instala um pacote Python"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} instalado com sucesso")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar {package}: {e}")
        return False

def main():
    """Instala todas as dependências necessárias"""
    packages = [
        "requests==2.31.0"
    ]
    
    print("🔧 Instalando dependências adicionais...")
    
    success = True
    for package in packages:
        if not install_package(package):
            success = False
    
    if success:
        print("✅ Todas as dependências instaladas com sucesso!")
    else:
        print("❌ Algumas dependências falharam")
        sys.exit(1)

if __name__ == "__main__":
    main()