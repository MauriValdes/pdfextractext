"""Configuración explícita de capacidades solo para el entorno de pruebas."""

import os


os.environ["MAX_ADMITTED_EXTRACTIONS"] = "2"
