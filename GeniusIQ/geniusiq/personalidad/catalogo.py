"""Lista de cuestionarios disponibles: personalidad (etapas 1 y 2) y tamizaje de salud mental (etapa 3)."""

from ..salud.tamizajes import TAMIZAJES
from .bigfive import BIG_FIVE
from .eneagrama import ENEAGRAMA
from .hexaco import HEXACO
from .laboral import PERFIL_LABORAL
from .tipos16 import TIPOS_16
from .valores import VALORES_CUESTIONARIO

CUESTIONARIOS = [BIG_FIVE, HEXACO, TIPOS_16, ENEAGRAMA, PERFIL_LABORAL, VALORES_CUESTIONARIO]
POR_CLAVE = {c.clave: c for c in CUESTIONARIOS + TAMIZAJES}
