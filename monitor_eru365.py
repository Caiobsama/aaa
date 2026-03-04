"""
Monitor de Vagas - ERU 365 (Relações Internacionais) - UFV 2026/1

Verifica a cada 30 minutos se há vagas livres na disciplina ERU 365
no site da DTI/UFV e envia notificação via Telegram.

COMO CONFIGURAR O TELEGRAM:
1. No Telegram, procure o bot @BotFather
2. Envie /newbot e siga as instruções para criar seu bot
3. Copie o TOKEN que ele vai te dar
4. Abra o seu bot no Telegram e envie qualquer mensagem (ex: "oi")
5. Acesse: https://api.telegram.org/bot<SEU_TOKEN>/getUpdates
6. Procure o "chat":{"id": XXXXXXX} — esse é seu CHAT_ID
7. Crie um arquivo .env baseado em .env.example e preencha TOKEN e CHAT_ID

COMO RODAR:
    pip install -r requirements.txt
    python3 monitor_eru365.py

Para rodar em background no Linux/Mac:
    nohup python3 monitor_eru365.py > monitor.log 2>&1 &

Para parar:
    kill $(pgrep -f monitor_eru365.py)
"""

import os
import sys
import logging
import requests
import time
from datetime import datetime
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: beautifulsoup4 not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

# Load environment variables from .env file
load_dotenv()

# ==============================================================
# CONFIGURATION
# ==============================================================

# Telegram (optional — leave empty to only display in terminal)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Discipline to monitor
DISCIPLINA_ALVO = os.getenv("DISCIPLINA_ALVO", "ERU 365").strip()

# URL of the schedule page
URL = "https://www.dti.ufv.br/horario/horario.asp?ano=2026&semestre=1&depto=eru"

# Check interval (in seconds)
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))
INTERVALO_SEGUNDOS = CHECK_INTERVAL_MINUTES * 60

# Optional file logging
LOG_FILE = os.getenv("LOG_FILE", "").strip()

# Max retries for network requests
MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]  # Exponential backoff in seconds

# ==============================================================
# LOGGING SETUP
# ==============================================================

def setup_logging() -> logging.Logger:
    """Configure logging with optional file output."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if configured)
    if LOG_FILE:
        try:
            file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not set up file logging: {e}")

    return logger


log = setup_logging()


# ==============================================================
# TELEGRAM NOTIFICATION
# ==============================================================


def enviar_telegram(mensagem: str) -> bool:
    """Sends message via Telegram Bot API with retry logic."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML",
    }

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(url, json=payload, timeout=15)
            resp.raise_for_status()
            log.info("Notificação Telegram enviada com sucesso.")
            return True
        except requests.exceptions.Timeout:
            log.warning(f"Telegram request timeout (attempt {attempt + 1}/{MAX_RETRIES})")
        except requests.exceptions.ConnectionError as e:
            log.warning(f"Telegram connection error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
        except Exception as e:
            log.error(f"Erro ao enviar Telegram: {e}")
            return False

        if attempt < MAX_RETRIES - 1:
            delay = RETRY_DELAYS[attempt]
            log.info(f"Retrying in {delay} seconds...")
            time.sleep(delay)

    return False


# ==============================================================
# WEB SCRAPING
# ==============================================================


def buscar_vagas() -> Optional[list]:
    """
    Fetches the schedule page from DTI/UFV and extracts target discipline info.
    Returns list of dicts with vacancy data or None on error.
    """
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(URL, timeout=30)
            resp.raise_for_status()
            html = resp.text
            break
        except requests.exceptions.Timeout:
            log.warning(f"Request timeout (attempt {attempt + 1}/{MAX_RETRIES})")
        except requests.exceptions.ConnectionError as e:
            log.warning(f"Connection error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
        except Exception as e:
            log.error(f"Erro ao acessar o site: {e}")
            return None

        if attempt < MAX_RETRIES - 1:
            delay = RETRY_DELAYS[attempt]
            log.info(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    else:
        return None

    try:
        soup = BeautifulSoup(html, "html.parser")
        resultados = []

        # Find all table rows
        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) >= 10:
                # Extract text and clean whitespace
                clean_cells = [cell.get_text(strip=True) for cell in cells]

                # Skip header row (first column is "Cod" for headers)
                if clean_cells[0] == "Cod":
                    continue

                # Check if this is the target discipline
                if DISCIPLINA_ALVO in clean_cells[0]:
                    resultados.append({
                        "codigo": clean_cells[0],
                        "disciplina": clean_cells[1],
                        "tipo": clean_cells[2],
                        "turma": clean_cells[3],
                        "horario": clean_cells[4],
                        "sala": clean_cells[5],
                        "vg_curso": clean_cells[6],
                        "vg_total": clean_cells[7],
                        "vg_livres": clean_cells[8],
                        "professor": clean_cells[9] if len(clean_cells) > 9 else "?",
                    })

        if not resultados:
            log.warning(f"Disciplina {DISCIPLINA_ALVO} não encontrada na página.")
            return None

        return resultados

    except Exception as e:
        log.error(f"Erro ao processar HTML: {e}")
        return None


# ==============================================================
# FORMATTING
# ==============================================================


def formatar_resultado(dados: list) -> str:
    """Formats the data for display."""
    linhas = [f"📚 Monitor {DISCIPLINA_ALVO} — {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"]
    for d in dados:
        vg_livres = d["vg_livres"]
        emoji = "🟢" if int(vg_livres) > 0 else "🔴"
        linhas.append(
            f"{emoji} {d['codigo']} - {d['disciplina']}\n"
            f"   Tipo: {d['tipo']} | Turma: {d['turma']}\n"
            f"   Horário: {d['horario']}\n"
            f"   Vagas Total: {d['vg_total']} | <b>Vagas Livres: {vg_livres}</b>\n"
        )
    return "\n".join(linhas)


# ==============================================================
# MONITORING LOGIC
# ==============================================================


class VagasMonitor:
    """Monitors vacancy status with state tracking."""

    def __init__(self):
        self.vagas_abertas_anterior = False

    def verificar(self) -> None:
        """Executes a single check."""
        log.info(f"Verificando vagas para {DISCIPLINA_ALVO}...")
        dados = buscar_vagas()

        if dados is None:
            msg = (
                f"⚠️ Não foi possível verificar {DISCIPLINA_ALVO} "
                "— erro ao acessar o site."
            )
            log.warning(msg)
            enviar_telegram(msg)
            return

        # Filter out invalid entries (with non-numeric vg_livres)
        dados_validos = []
        for d in dados:
            try:
                int(d["vg_livres"])
                dados_validos.append(d)
            except (ValueError, KeyError):
                pass

        if not dados_validos:
            log.warning(f"Nenhuma vaga válida encontrada para {DISCIPLINA_ALVO}.")
            return

        dados = dados_validos
        texto = formatar_resultado(dados)

        # Check if there are available vacancies
        try:
            tem_vagas = any(int(d["vg_livres"]) > 0 for d in dados)
        except (ValueError, KeyError) as e:
            log.error(f"Erro ao processar vagas: {e}")
            return

        if tem_vagas:
            log.info("🟢 VAGAS DISPONÍVEIS!")
            if not self.vagas_abertas_anterior:
                # Changed from no vacancy → vacancy: notify
                print("\n" + "=" * 60)
                print("🚨🚨🚨  VAGAS ABERTAS!  🚨🚨🚨")
                print("=" * 60)
                print(texto.replace("<b>", "").replace("</b>", ""))
                print("=" * 60 + "\n")
                enviar_telegram(f"🚨🚨🚨 VAGAS ABERTAS!\n\n{texto}")
            else:
                log.info("(vagas ainda abertas, já notificado)")
        else:
            log.info("🔴 Sem vagas livres no momento.")
            if self.vagas_abertas_anterior:
                # Changed from vacancy → no vacancy: notify closure
                msg = (
                    f"🔴 Vagas fecharam novamente — {DISCIPLINA_ALVO}\n"
                    f"({datetime.now().strftime('%d/%m/%Y %H:%M')})"
                )
                print(msg)
                enviar_telegram(msg)

        self.vagas_abertas_anterior = tem_vagas


# ==============================================================
# MAIN
# ==============================================================


def main() -> None:
    """Main loop."""
    print("=" * 60)
    print(f"  Monitor de Vagas — {DISCIPLINA_ALVO}")
    print(f"  UFV 2026/1 — Departamento ERU")
    print(f"  Verificação a cada {CHECK_INTERVAL_MINUTES} minutos")
    telegram_status = "Configurado ✅" if TELEGRAM_TOKEN else "Não configurado ❌"
    print(f"  Telegram: {telegram_status}")
    print("=" * 60)
    print()

    monitor = VagasMonitor()

    # First check immediately
    monitor.verificar()

    # Main loop
    try:
        while True:
            log.info(f"Próxima verificação em {CHECK_INTERVAL_MINUTES} minutos...")
            time.sleep(INTERVALO_SEGUNDOS)
            monitor.verificar()
    except KeyboardInterrupt:
        log.info("Monitor finalizado pelo usuário.")
        sys.exit(0)


if __name__ == "__main__":
    main()
