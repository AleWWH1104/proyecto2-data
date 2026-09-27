"""Pruebas de humo offline para las fábricas de modelos reales."""

import unittest

import torch

from src.models import FABRICAS_MODELOS, crear_modelo
from src.training import adaptar_logits


class ModelosTest(unittest.TestCase):
    def test_fabricas_generan_logits_binarios_finitos_sin_red(self) -> None:
        entrada = torch.randn(1, 3, 64, 64)
        mascara = torch.zeros(1, 1, 64, 64)

        for nombre in FABRICAS_MODELOS:
            with self.subTest(modelo=nombre):
                modelo = crear_modelo(nombre, pesos_preentrenados=False).eval()
                with torch.inference_mode():
                    logits = adaptar_logits(modelo(entrada), mascara)

                self.assertEqual(logits.shape, (1, 1, 64, 64))
                self.assertTrue(torch.isfinite(logits).all())

    def test_rechaza_nombre_desconocido(self) -> None:
        with self.assertRaisesRegex(ValueError, "Modelo desconocido"):
            crear_modelo("inexistente")


if __name__ == "__main__":
    unittest.main()
