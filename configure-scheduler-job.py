#!/usr/bin/env python3
"""
Script para configurar job do Heroku Scheduler via API

Uso:
    python configure-scheduler-job.py
    
Requer:
    - Heroku CLI instalado e autenticado
    - Heroku Scheduler add-on instalado
"""

import subprocess
import json
import sys

def run_command(cmd):
    """Executa comando e retorna output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar comando: {cmd}")
        print(f"   {e.stderr}")
        return None

def get_heroku_token():
    """Obtém token de autenticação do Heroku"""
    print("🔑 Obtendo token de autenticação...")
    token = run_command("heroku auth:token")
    if token:
        print("✅ Token obtido")
        return token
    return None

def get_app_id():
    """Obtém ID da aplicação"""
    print("🔍 Obtendo ID da aplicação...")
    output = run_command("heroku apps:info lwksistemas --json")
    if output:
        data = json.loads(output)
        app_id = data.get('app', {}).get('id')
        if app_id:
            print(f"✅ App ID: {app_id}")
            return app_id
    return None

def get_scheduler_addon_id():
    """Obtém ID do add-on Scheduler"""
    print("🔍 Obtendo ID do Scheduler add-on...")
    output = run_command("heroku addons:info scheduler -a lwksistemas --json")
    if output:
        data = json.loads(output)
        addon_id = data.get('id')
        if addon_id:
            print(f"✅ Scheduler ID: {addon_id}")
            return addon_id
    return None

def create_scheduler_job(token, addon_id):
    """Cria job no Heroku Scheduler via API"""
    print("\n📋 Criando job no Heroku Scheduler...")
    
    # Comando a ser executado
    command = "python manage.py detect_security_violations"
    
    # Frequência: a cada 10 minutos
    frequency = "every_10_minutes"
    
    # Construir comando curl
    curl_cmd = f"""curl -X POST https://api.heroku.com/addons/{addon_id}/actions/create-job \\
  -H "Authorization: Bearer {token}" \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/vnd.heroku+json; version=3" \\
  -d '{{"command": "{command}", "frequency": "{frequency}", "dyno_size": "standard-1x"}}'"""
    
    print(f"\n📝 Configuração do job:")
    print(f"   Comando: {command}")
    print(f"   Frequência: {frequency}")
    print(f"   Dyno Size: standard-1x")
    print()
    
    result = run_command(curl_cmd)
    
    if result:
        try:
            data = json.loads(result)
            if 'id' in data:
                print("✅ Job criado com sucesso!")
                print(f"   Job ID: {data.get('id')}")
                return True
            else:
                print("⚠️  Resposta da API:")
                print(f"   {result}")
        except json.JSONDecodeError:
            print("⚠️  Resposta da API (não é JSON):")
            print(f"   {result}")
    
    return False

def list_scheduler_jobs(token, addon_id):
    """Lista jobs existentes no Scheduler"""
    print("\n📋 Listando jobs existentes...")
    
    curl_cmd = f"""curl -X GET https://api.heroku.com/addons/{addon_id}/actions/list-jobs \\
  -H "Authorization: Bearer {token}" \\
  -H "Accept: application/vnd.heroku+json; version=3" """
    
    result = run_command(curl_cmd)
    
    if result:
        try:
            data = json.loads(result)
            if isinstance(data, list) and len(data) > 0:
                print(f"✅ {len(data)} job(s) encontrado(s):")
                for job in data:
                    print(f"   - {job.get('command')} ({job.get('frequency')})")
                return data
            else:
                print("ℹ️  Nenhum job configurado ainda")
        except json.JSONDecodeError:
            print("⚠️  Resposta da API:")
            print(f"   {result}")
    
    return []

def main():
    print("🔒 Configuração do Heroku Scheduler - Detecção de Violações de Segurança")
    print("=" * 80)
    print()
    
    # Verificar se Heroku CLI está instalado
    if not run_command("which heroku"):
        print("❌ Heroku CLI não encontrado!")
        print("   Instale em: https://devcenter.heroku.com/articles/heroku-cli")
        sys.exit(1)
    
    print("✅ Heroku CLI encontrado")
    print()
    
    # Obter token
    token = get_heroku_token()
    if not token:
        print("❌ Não foi possível obter token de autenticação")
        print("   Execute: heroku login")
        sys.exit(1)
    
    # Obter App ID
    app_id = get_app_id()
    if not app_id:
        print("❌ Não foi possível obter ID da aplicação")
        sys.exit(1)
    
    # Obter Scheduler Add-on ID
    addon_id = get_scheduler_addon_id()
    if not addon_id:
        print("❌ Heroku Scheduler não está instalado")
        print("   Execute: heroku addons:create scheduler:standard -a lwksistemas")
        sys.exit(1)
    
    # Listar jobs existentes
    existing_jobs = list_scheduler_jobs(token, addon_id)
    
    # Verificar se job já existe
    job_exists = any(
        'detect_security_violations' in job.get('command', '')
        for job in existing_jobs
    )
    
    if job_exists:
        print("\n⚠️  Job de detecção de violações já existe!")
        print("   Não é necessário criar novamente.")
        print()
        print("📊 Para verificar o status:")
        print("   heroku run python manage.py security_status -a lwksistemas")
        sys.exit(0)
    
    # Criar job
    print("\n⚠️  NOTA: A API do Heroku Scheduler pode não estar disponível via CLI.")
    print("   Se o comando falhar, você precisará configurar manualmente via dashboard.")
    print()
    
    input("Pressione ENTER para continuar ou Ctrl+C para cancelar...")
    print()
    
    success = create_scheduler_job(token, addon_id)
    
    if success:
        print("\n✅ Configuração concluída com sucesso!")
        print()
        print("🧪 TESTAR AGORA:")
        print("   heroku run python manage.py detect_security_violations -a lwksistemas")
        print()
        print("📊 VERIFICAR STATUS:")
        print("   heroku run python manage.py security_status -a lwksistemas")
        print()
        print("📝 VER LOGS:")
        print("   heroku logs --tail --ps scheduler -a lwksistemas")
    else:
        print("\n⚠️  Não foi possível criar o job via API.")
        print()
        print("📋 CONFIGURAÇÃO MANUAL:")
        print("   1. Abra o dashboard: heroku addons:open scheduler -a lwksistemas")
        print("   2. Clique em 'Create job'")
        print("   3. Configure:")
        print("      - Comando: python manage.py detect_security_violations")
        print("      - Frequência: Every 10 minutes")
        print("      - Dyno Size: Standard-1X")
        print("   4. Clique em 'Save Job'")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário")
        sys.exit(1)
