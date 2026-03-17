# auth.py
import requests
from playwright.sync_api import sync_playwright
from time import sleep
import re
import random

# ====================== CONFIGURAÇÃO .ENV ======================
from dotenv import load_dotenv
import os

load_dotenv()  # Carrega o arquivo .env automaticamente

# Pega as credenciais do .env
LOGIN_URL = os.getenv("LOGIN_URL")
USER      = os.getenv("USER")
PASS      = os.getenv("PASS")

# Validação de segurança (evita rodar com credenciais vazias)
if not all([LOGIN_URL, USER, PASS]):
    raise ValueError(
        "❌ Alguma variável está faltando no arquivo .env!\n"
        "Verifique se ele contém:\n"
        "LOGIN_URL=...\n"
        "USER=...\n"
        "PASS=..."
    )
# ============================================================


def human_mouse_move(page, steps=5):
    """Simula movimentos humanos do mouse pela página"""
    for _ in range(steps):
        x = random.randint(300, 900)
        y = random.randint(200, 600)
        page.mouse.move(x, y)
        sleep(random.uniform(0.1, 0.3))


def get_authenticated_session() -> requests.Session:
    """Retorna uma sessão requests já autenticada"""

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("🌐 Acessando página de login...")
        page.goto(LOGIN_URL, wait_until="networkidle")

        # 1️⃣ Movimentos de mouse ANTES de digitar
        print("🖱️  Simulando comportamento humano...")
        human_mouse_move(page, steps=6)
        sleep(1.5)

        # Preenche usuário
        user_field = page.get_by_role("textbox", name=re.compile("usuário", re.IGNORECASE))
        user_field.click()
        sleep(0.3)
        user_field.type(USER, delay=100)

        # Movimento entre os campos
        human_mouse_move(page, steps=3)
        sleep(0.5)

        # Preenche senha
        pass_field = page.get_by_role("textbox", name=re.compile("senha", re.IGNORECASE))
        pass_field.click()
        sleep(0.3)
        pass_field.type(PASS, delay=120)

        # 2️⃣ Pausa longa — mosparo
        print("⏳ Aguardando mosparo inicializar e analisar os campos...")
        page.wait_for_selector(".mosparo__checkbox", state="visible")
        human_mouse_move(page, steps=4)
        sleep(3)

        # 3️⃣ Move o mouse até o checkbox
        checkbox = page.locator(".mosparo__checkbox")
        box = checkbox.bounding_box()
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=10)
        sleep(0.5)

        print("☑️  Clicando no mosparo...")
        checkbox.click()

        # 4️⃣ Espera o token
        print("⏳ Aguardando token de validação do mosparo...")
        page.wait_for_function(
            """() => {
                const input = document.querySelector('input[name="_mosparo_submitToken"], input[name*="mosparo"]');
                return input && input.value && input.value.length > 0;
            }""",
            timeout=15000
        )
        print("✅ Token mosparo gerado!")
        sleep(0.8)

        # Clica em acessar
        print("🔐 Clicando em acessar...")
        page.locator("button:has-text('acessar')").click()

        # Espera redirecionamento
        try:
            page.wait_for_url(
                lambda url: "acesso/login" not in url.lower(),
                timeout=15000
            )
        except:
            pass

        print(f"📍 URL atual: {page.url}")

        if "acesso/login" in page.url.lower():
            erro = page.locator(".alert, .error, .mensagem-erro, [class*='erro']").all_inner_texts()
            print(f"❌ Mensagens na página: {erro}")
            raise Exception("❌ Login falhou")

        print("🎉 Login realizado com sucesso!")
        print("👀 Mantendo browser aberto 5s pra você confirmar...")
        sleep(5)

        # Cria sessão requests com os cookies
        cookies = context.cookies()
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(
                name=cookie["name"],
                value=cookie["value"],
                domain=cookie.get("domain", ""),
                path=cookie.get("path", "/")
            )
        session.headers.update({"User-Agent": page.evaluate("() => navigator.userAgent")})

        browser.close()
        return session


if __name__ == "__main__":
    session = get_authenticated_session()
    print("Session pronta! Cookies:", len(session.cookies))