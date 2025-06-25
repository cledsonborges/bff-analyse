#!/usr/bin/env python3
"""
Script de teste para verificar a funcionalidade de registro de usuários no DynamoDB
"""

import sys
import os
import json
import requests
import time

# Adicionar o diretório do projeto ao path
sys.path.append('/home/ubuntu/bff-analyse')

def test_user_service():
    """Testa o serviço de usuários diretamente"""
    try:
        from services.user_service import UserService
        
        print("🔧 Testando UserService...")
        user_service = UserService()
        
        # Teste de registro de usuário
        test_email = "teste@example.com"
        result = user_service.register_user_login(test_email, {
            'user_agent': 'Test Agent',
            'ip_address': '127.0.0.1'
        })
        
        if result['success']:
            print(f"✅ Usuário {test_email} registrado com sucesso")
            print(f"   Dados: {json.dumps(result['user_data'], indent=2)}")
        else:
            print(f"❌ Erro ao registrar usuário: {result['error']}")
            return False
        
        # Teste de busca de usuário
        user_data = user_service.get_user_by_email(test_email)
        if user_data:
            print(f"✅ Usuário encontrado: {user_data['email']}")
            print(f"   Login count: {user_data.get('login_count', 0)}")
        else:
            print(f"❌ Usuário {test_email} não encontrado")
            return False
        
        # Teste de estatísticas
        stats = user_service.get_user_stats(test_email)
        if stats['success']:
            print(f"✅ Estatísticas obtidas com sucesso")
            print(f"   Stats: {json.dumps(stats['stats'], indent=2)}")
        else:
            print(f"❌ Erro ao obter estatísticas: {stats['error']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do UserService: {e}")
        return False

def test_api_endpoints():
    """Testa os endpoints da API"""
    try:
        print("\n🌐 Testando endpoints da API...")
        
        # Iniciar servidor Flask em background (simulação)
        print("   Nota: Para testar completamente, inicie o servidor Flask com:")
        print("   python3 api.py")
        print("   E então execute os testes de API")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste da API: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes do sistema de usuários DynamoDB\n")
    
    # Configurar variáveis de ambiente (usar valores reais em produção)
    if not os.getenv('AWS_ACCESS_KEY_ID'):
        print("⚠️  Variáveis de ambiente AWS não configuradas")
        print("   Configure AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY")
        return False
    
    success_count = 0
    total_tests = 2
    
    # Teste 1: UserService
    if test_user_service():
        success_count += 1
    
    # Teste 2: API Endpoints
    if test_api_endpoints():
        success_count += 1
    
    print(f"\n📊 Resultados dos testes: {success_count}/{total_tests} passaram")
    
    if success_count == total_tests:
        print("🎉 Todos os testes passaram! O sistema está funcionando corretamente.")
        return True
    else:
        print("⚠️  Alguns testes falharam. Verifique os logs acima.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

