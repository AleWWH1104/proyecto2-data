"""Contrato offline para la sección de entrenamiento del notebook."""

import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
RUTA_NOTEBOOK = RAIZ / "proyecto2-resultados.ipynb"


class CargadoresVigilados(dict):
    """Registra las particiones consultadas durante la ejecución del contrato."""

    def __init__(self) -> None:
        super().__init__(train=object(), val=object(), test=object())
        self.accesos: list[str] = []

    def __getitem__(self, clave: str) -> object:
        self.accesos.append(clave)
        return super().__getitem__(clave)


class NotebookContractTest(unittest.TestCase):
    def test_seccion_3_es_segura_con_banderas_predeterminadas(self) -> None:
        notebook = json.loads(RUTA_NOTEBOOK.read_text(encoding="utf-8"))
        celdas_codigo = [
            celda for celda in notebook["cells"] if celda["cell_type"] == "code"
        ]

        for celda in celdas_codigo:
            compile(
                "".join(celda["source"]),
                f"{RUTA_NOTEBOOK.name}:{celda['id']}",
                "exec",
            )

        celdas_seccion_3 = []
        dentro_seccion_3 = False
        for celda in notebook["cells"]:
            fuente = "".join(celda.get("source", []))
            if celda["cell_type"] == "markdown" and "## 3. Entrenamiento" in fuente:
                dentro_seccion_3 = True
                continue
            if celda["cell_type"] == "markdown" and "## 4. Evaluación" in fuente:
                break
            if dentro_seccion_3 and celda["cell_type"] == "code":
                celdas_seccion_3.append(celda)

        codigo_seccion_3 = "\n".join(
            "".join(celda["source"]) for celda in celdas_seccion_3
        )
        self.assertNotRegex(
            codigo_seccion_3,
            re.compile(r"(?:loaders|cargadores_entrenamiento)\s*\[\s*['\"]test['\"]\s*\]"),
        )

        cargadores = CargadoresVigilados()
        preparar_cache = Mock(side_effect=AssertionError("No debe preparar caché"))
        crear_dataloaders = Mock(side_effect=AssertionError("No debe crear cargadores"))

        with tempfile.TemporaryDirectory() as directorio:
            temporal = Path(directorio)
            data_dir = temporal / "data"
            contexto = {
                "DATA_DIR": str(data_dir),
                "IMG_DIR": str(data_dir / "train_images"),
                "HAY_IMAGENES": False,
                "loaders": cargadores,
                "pd": pd,
                "pp": SimpleNamespace(
                    preparar_cache=preparar_cache,
                    crear_dataloaders=crear_dataloaders,
                ),
                "splits": pd.DataFrame(),
                "train": pd.DataFrame(),
            }
            entorno_offline = {
                "HF_HOME": str(temporal / "hf-cache"),
                "HF_HUB_OFFLINE": "1",
                "TORCH_HOME": str(temporal / "torch-cache"),
                "TRANSFORMERS_OFFLINE": "1",
            }

            with (
                patch.dict(os.environ, entorno_offline),
                patch(
                    "src.models.crear_modelo",
                    side_effect=AssertionError("No debe crear modelos ni descargar pesos"),
                ) as crear_modelo,
                patch(
                    "src.training.entrenar_modelo",
                    side_effect=AssertionError("No debe entrenar modelos"),
                ) as entrenar_modelo,
                patch(
                    "src.training.ejecutar_preflight_cuda",
                    side_effect=AssertionError("No debe acceder a CUDA"),
                ) as ejecutar_preflight_cuda,
            ):
                for celda in celdas_seccion_3:
                    exec(
                        compile(
                            "".join(celda["source"]),
                            f"{RUTA_NOTEBOOK.name}:{celda['id']}",
                            "exec",
                        ),
                        contexto,
                    )

            self.assertFalse(contexto["EJECUTAR_PREPARACION"])
            self.assertFalse(contexto["EJECUTAR_ENTRENAMIENTO"])
            self.assertEqual(contexto["RESOLUCION"], 384)
            self.assertEqual(contexto["BATCH_ENTRENAMIENTO"], 1)
            self.assertEqual(contexto["ACUMULACION_GRADIENTES"], 2)
            self.assertEqual(contexto["BATCH_EFECTIVO"], 2)
            self.assertFalse((data_dir / "cache_384").exists())
            self.assertFalse((data_dir / "artefactos_entrenamiento").exists())
            self.assertFalse((temporal / "hf-cache").exists())
            self.assertFalse((temporal / "torch-cache").exists())
            self.assertNotIn("test", cargadores.accesos)
            preparar_cache.assert_not_called()
            crear_dataloaders.assert_not_called()
            crear_modelo.assert_not_called()
            entrenar_modelo.assert_not_called()
            ejecutar_preflight_cuda.assert_not_called()

    def test_preflight_aparece_antes_del_entrenamiento_y_de_los_artefactos(self) -> None:
        notebook = json.loads(RUTA_NOTEBOOK.read_text(encoding="utf-8"))
        celda_entrenamiento = next(
            "".join(celda["source"])
            for celda in notebook["cells"]
            if celda["cell_type"] == "code"
            and "if EJECUTAR_ENTRENAMIENTO:" in "".join(celda["source"])
        )

        posicion_preflight = celda_entrenamiento.index("resultados_preflight = ejecutar_preflight_cuda")
        posicion_artefactos = celda_entrenamiento.index("RUTA_ARTEFACTOS.mkdir")
        posicion_entrenamiento = celda_entrenamiento.index("resultado = entrenar_modelo")

        self.assertLess(posicion_preflight, posicion_artefactos)
        self.assertLess(posicion_preflight, posicion_entrenamiento)
        self.assertIn("acumulacion_gradientes=ACUMULACION_GRADIENTES", celda_entrenamiento)


if __name__ == "__main__":
    unittest.main()
