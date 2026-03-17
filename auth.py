# auth.py
import requests
from playwright.sync_api import sync_playwright
from time import sleep
import re
import random
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

LOGIN_URL = os.getenv("LOGIN_URL")
USER      = os.getenv("USER")
PASS      = os.getenv("PASS")
COOKIES_FILE = "session_cookies.json"  # ← arquivo onde salva os cookies

if not all([LOGIN_URL, USER, PASS]):
    raise ValueError("❌ Variáveis faltando no .env!")


def save_cookies(session: requests.Session):
    """Salva cookies + timestamp no disco"""
    data = {
        "saved_at": datetime.now().isoformat(),
        "cookies": [
            {"name": c.name, "value": c.value, "domain": c.domain, "path": c.path}
            for c in session.cookies
        ]
    }
    with open(COOKIES_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"💾 Cookies salvos em '{COOKIES_FILE}'")


def load_cookies() -> requests.Session | None:
    """Carrega cookies do disco se existirem e forem recentes (menos de 8h)"""
    if not os.path.exists(COOKIES_FILE):
        return None

    with open(COOKIES_FILE, "r") as f:
        data = json.load(f)

    saved_at = datetime.fromisoformat(data["saved_at"])
    idade = datetime.now() - saved_at

    if idade > timedelta(hours=8):  # ← ajuste o tempo de expiração aqui
        print(f"⚠️  Cookies com {int(idade.total_seconds() / 3600)}h — fazendo novo login...")
        return None

    session = requests.Session()
    for c in data["cookies"]:
        session.cookies.set(c["name"], c["value"], domain=c["domain"], path=c["path"])
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    })

    print(f"✅ Cookies carregados do disco! (salvos há {int(idade.total_seconds() / 60)} min)")
    return session


def validate_session(session: requests.Session) -> bool:
    """Confirma se a session ainda é válida fazendo uma requisição real"""
    try:
        resp = session.get(
            "https://www.corretorrodrigomedeiros.com.br/intranet/index/",
            timeout=10,
            allow_redirects=True
        )
        is_valid = resp.status_code == 200 and "login" not in resp.url
        if is_valid:
            print("✅ Session validada com requisição real!")
        else:
            print(f"⚠️  Session inválida — redirecionou para: {resp.url}")
        return is_valid
    except Exception as e:
        print(f"⚠️  Erro ao validar session: {e}")
        return False


def human_mouse_move(page, steps=5):
    for _ in range(steps):
        x = random.randint(300, 900)
        y = random.randint(200, 600)
        page.mouse.move(x, y)
        sleep(random.uniform(0.1, 0.3))


def _do_login() -> requests.Session:
    """Faz o login via Playwright e retorna a session"""
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

        print("🖱️  Simulando comportamento humano...")
        human_mouse_move(page, steps=6)
        sleep(1.5)

        user_field = page.get_by_role("textbox", name=re.compile("usuário", re.IGNORECASE))
        user_field.click()
        sleep(0.3)
        user_field.type(USER, delay=100)

        human_mouse_move(page, steps=3)
        sleep(0.5)

        pass_field = page.get_by_role("textbox", name=re.compile("senha", re.IGNORECASE))
        pass_field.click()
        sleep(0.3)
        pass_field.type(PASS, delay=120)

        print("⏳ Aguardando mosparo...")
        page.wait_for_selector(".mosparo__checkbox", state="visible")
        human_mouse_move(page, steps=4)
        sleep(3)

        checkbox = page.locator(".mosparo__checkbox")
        box = checkbox.bounding_box()
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=10)
        sleep(0.5)

        print("☑️  Clicando no mosparo...")
        checkbox.click()

        print("⏳ Aguardando token...")
        page.wait_for_function(
            """() => {
                const input = document.querySelector('input[name="_mosparo_submitToken"], input[name*="mosparo"]');
                return input && input.value && input.value.length > 0;
            }""",
            timeout=15000
        )
        print("✅ Token mosparo gerado!")
        sleep(0.8)

        print("🔐 Clicando em acessar...")
        page.locator("button:has-text('acessar')").click()

        try:
            page.wait_for_url(lambda url: "acesso/login" not in url.lower(), timeout=15000)
        except:
            pass

        print(f"📍 URL atual: {page.url}")

        if "acesso/login" in page.url.lower():
            raise Exception("❌ Login falhou")

        print("🎉 Login realizado com sucesso!")
        sleep(3)

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


def get_authenticated_session() -> requests.Session:
    """
    Tenta usar cookies salvos primeiro.
    Só faz login via Playwright se não tiver ou estiverem expirados/inválidos.
    """
    # 1. Tenta carregar do disco
    session = load_cookies()

    # 2. Valida se ainda funciona
    if session and validate_session(session):
        return session

    # 3. Faz login completo e salva
    print("🔑 Fazendo login completo via Playwright...")
    session = _do_login()
    save_cookies(session)
    return session


if __name__ == "__main__":
    session = get_authenticated_session()
    print("Session pronta! Cookies:", len(session.cookies))
