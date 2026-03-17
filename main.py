# main.py
from auth import get_authenticated_session
from time import sleep
import random

def main():
    print("🚀 Iniciando automação de atualização de imóveis...")
    
    # ==================== 1. OBTÉM A SESSÃO AUTENTICADA ====================
    session = get_authenticated_session()
    
    print("✅ Sessão autenticada com sucesso! Cookies carregados.")
    print(f"   Cookies na sessão: {len(session.cookies)}")
    
    # ==================== 2. LISTA DE IDs (você pode mudar depois) ====================
    # Por enquanto vamos só até 10 pra testar rápido
    # Depois troque pra range(1, 1500) ou carregue de um CSV/Excel
    ids_para_atualizar = range(1, 11)   # ← MUDE AQUI QUANDO QUISER
    
    # ==================== 3. LOOP (ainda placeholder - vamos preencher depois) ====================
    for imovel_id in ids_para_atualizar:
        print(f"📋 Processando imóvel ID: {imovel_id}")
        
        # ←←← AQUI VAI VIR TODO O CÓDIGO DO imoveis.py depois
        # html = get_imovel_form(session, imovel_id)
        # payload = parse_form(html)
        # update_imovel(session, imovel_id, payload)
        
        # Delay aleatório (anti-ban)
        delay = random.uniform(3.0, 7.0)
        print(f"   ⏳ Aguardando {delay:.1f}s antes do próximo...")
        sleep(delay)
    
    print("🎉 Automação finalizada!")


if __name__ == "__main__":
    main()