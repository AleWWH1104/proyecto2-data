"""Pruebas mínimas de las métricas de prueba."""

import unittest

import torch

from src.evaluation import dice_por_imagen, iou_por_imagen
from src.training import dice_binario


class MetricasTest(unittest.TestCase):
    def test_promedio_coincide_con_el_dice_del_entrenamiento(self):
        torch.manual_seed(0)
        mascaras = (torch.rand(5, 1, 8, 8) > 0.5).float()
        logits = torch.randn(5, 1, 8, 8)
        self.assertAlmostEqual(
            float(dice_por_imagen(logits, mascaras).mean()),
            float(dice_binario(logits, mascaras)),
            places=6,
        )

    def test_mascara_y_prediccion_vacias_dan_uno(self):
        mascaras = torch.zeros(1, 1, 4, 4)
        logits = torch.full((1, 1, 4, 4), -10.0)
        self.assertAlmostEqual(float(dice_por_imagen(logits, mascaras)[0]), 1.0)
        self.assertAlmostEqual(float(iou_por_imagen(logits, mascaras)[0]), 1.0)

    def test_mascara_vacia_con_falso_positivo_da_cero(self):
        mascaras = torch.zeros(1, 1, 4, 4)
        logits = torch.full((1, 1, 4, 4), 10.0)
        self.assertAlmostEqual(float(dice_por_imagen(logits, mascaras)[0]), 0.0)
        self.assertAlmostEqual(float(iou_por_imagen(logits, mascaras)[0]), 0.0)

    def test_dice_es_mayor_o_igual_que_iou(self):
        torch.manual_seed(1)
        mascaras = (torch.rand(6, 1, 8, 8) > 0.5).float()
        logits = torch.randn(6, 1, 8, 8)
        dados = dice_por_imagen(logits, mascaras)
        ious = iou_por_imagen(logits, mascaras)
        self.assertTrue(bool((dados >= ious - 1e-6).all()))


if __name__ == "__main__":
    unittest.main()
