"""
SIA-T: hora oficial del sistema.

El servidor de la demostración funciona con la hora universal (UTC). Todas las fechas que el sistema
guarda o muestra usan la hora de Lima, que es UTC−5 todo el año (Perú no cambia de horario).
"""

from datetime import datetime, timedelta, timezone

LIMA = timezone(timedelta(hours=-5), "America/Lima")


def ahora() -> datetime:
    """Fecha y hora actuales de Lima, sin zona horaria adjunta (como se guardan en la base)."""
    return datetime.now(LIMA).replace(tzinfo=None)
