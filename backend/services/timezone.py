from datetime import datetime
import pytz

# fuso horário do Brasil (SP/RJ/PR/SC/RS etc.)
BR_TZ = pytz.timezone("America/Sao_Paulo")

def now_brazil():
    """Retorna datetime com fuso horário do Brasil."""
    return datetime.now(BR_TZ)

def today_brazil_str():
    """Retorna YYYY-MM-DD no fuso do Brasil."""
    return now_brazil().strftime("%Y-%m-%d")
