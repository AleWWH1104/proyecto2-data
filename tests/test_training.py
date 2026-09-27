"""Pruebas unitarias del módulo común de entrenamiento."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import cv2
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from src.preprocess import crear_dataloaders
from src.training import (
    PerdidaBCEDice,
    adaptar_logits,
    cargar_checkpoint,
    entrenar_modelo,
    ejecutar_preflight_cuda,
    ejecutar_epoca,
)


class DatasetMinimo(Dataset):
    def __init__(self, cantidad: int = 3) -> None:
        self.imagenes = torch.zeros(cantidad, 1, 4, 4)
        self.mascaras = torch.zeros(cantidad, 1, 4, 4)

    def __len__(self) -> int:
        return len(self.imagenes)

    def __getitem__(self, indice: int) -> dict[str, torch.Tensor]:
        return {
            "image": self.imagenes[indice],
            "mask": self.mascaras[indice],
        }


class ModeloMinimo(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.capa = nn.Conv2d(1, 1, kernel_size=1)
        nn.init.zeros_(self.capa.weight)
        nn.init.zeros_(self.capa.bias)

    def forward(self, imagenes: torch.Tensor) -> torch.Tensor:
        return self.capa(imagenes)


class SGDContado(torch.optim.SGD):
    def __init__(self, parametros: object) -> None:
        super().__init__(parametros, lr=0.1)
        self.pasos = 0

    def step(self, closure: object = None) -> object:
        self.pasos += 1
        return super().step(closure)


class TrainingTest(unittest.TestCase):
    def test_acumulacion_hace_un_paso_por_ventana_incluida_la_parcial(self) -> None:
        cargador = DataLoader(DatasetMinimo(5), batch_size=1, shuffle=False)
        modelo = ModeloMinimo()
        optimizador = SGDContado(modelo.parameters())

        ejecutar_epoca(
            modelo,
            cargador,
            PerdidaBCEDice(),
            dispositivo="cpu",
            optimizador=optimizador,
            acumulacion_gradientes=2,
        )

        self.assertEqual(optimizador.pasos, 3)
        self.assertTrue(all(parametro.grad is None for parametro in modelo.parameters()))

    def test_acumulacion_uno_conserva_un_paso_por_lote(self) -> None:
        cargador = DataLoader(DatasetMinimo(3), batch_size=1, shuffle=False)
        modelo = ModeloMinimo()
        optimizador = SGDContado(modelo.parameters())

        ejecutar_epoca(
            modelo,
            cargador,
            PerdidaBCEDice(),
            dispositivo="cpu",
            optimizador=optimizador,
        )

        self.assertEqual(optimizador.pasos, 3)

    def test_rechaza_acumulacion_invalida(self) -> None:
        cargador = DataLoader(DatasetMinimo(2), batch_size=1, shuffle=False)

        for valor in (0, -1, 1.5, True):
            with self.subTest(valor=valor):
                with self.assertRaisesRegex(ValueError, "acumulacion_gradientes"):
                    ejecutar_epoca(
                        ModeloMinimo(),
                        cargador,
                        PerdidaBCEDice(),
                        dispositivo="cpu",
                        acumulacion_gradientes=valor,
                    )

    def test_preflight_orquesta_modelos_sin_fingir_cuda(self) -> None:
        eventos = []

        def crear(nombre: str) -> nn.Module:
            eventos.append(("crear", nombre))
            modelo = ModeloMinimo()
            modelo.nombre_preflight = nombre
            return modelo

        def medir(**argumentos: object) -> dict[str, float]:
            modelo = argumentos["modelo"]
            eventos.append(("medir", modelo.nombre_preflight))
            return {"pico_asignado_mib": 100.0, "pico_reservado_mib": 120.0}

        resultado = ejecutar_preflight_cuda(
            ["modelo_a", "modelo_b"],
            crear,
            resolucion=32,
            medidor=medir,
        )

        self.assertEqual(
            eventos,
            [
                ("crear", "modelo_a"),
                ("medir", "modelo_a"),
                ("crear", "modelo_b"),
                ("medir", "modelo_b"),
            ],
        )
        self.assertEqual(resultado["modelo"].tolist(), ["modelo_a", "modelo_b"])

    def test_preflight_real_requiere_cuda_disponible(self) -> None:
        fabrica = Mock(side_effect=AssertionError("No debe crear un modelo"))

        with patch("src.training.torch.cuda.is_available", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "requiere una GPU CUDA"):
                ejecutar_preflight_cuda(
                    ["unet_resnet34"],
                    fabrica,
                    resolucion=384,
                )

        fabrica.assert_not_called()

    def test_preflight_convierte_oom_en_fallo_accionable(self) -> None:
        medidor = Mock(side_effect=torch.cuda.OutOfMemoryError("CUDA out of memory"))

        with self.assertRaisesRegex(RuntimeError, "no inicie el entrenamiento completo"):
            ejecutar_preflight_cuda(
                ["unet_resnet34"],
                lambda nombre: ModeloMinimo(),
                resolucion=384,
                medidor=medidor,
            )

    def test_rechaza_mejora_minima_negativa(self) -> None:
        cargador = DataLoader(DatasetMinimo(2), batch_size=2, shuffle=False)

        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "modelo.pt"
            with self.assertRaisesRegex(ValueError, "mejora_minima"):
                entrenar_modelo(
                    ModeloMinimo(),
                    cargador,
                    cargador,
                    ruta,
                    mejora_minima=-0.01,
                )

            self.assertFalse(ruta.exists())

    def test_dataloader_conserva_ultimo_lote_de_entrenamiento(self) -> None:
        filas = [
            {"id": indice, "organ": "kidney", "split": split}
            for indice, split in enumerate(["train"] * 5 + ["val", "test"])
        ]

        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio)
            for fila in filas:
                imagen = np.zeros((8, 8, 3), dtype=np.uint8)
                mascara = np.zeros((8, 8), dtype=np.uint8)
                cv2.imwrite(str(ruta / f"{fila['id']}.png"), imagen)
                cv2.imwrite(str(ruta / f"{fila['id']}_mask.png"), mascara)

            cargador = crear_dataloaders(
                pd.DataFrame(filas),
                ruta,
                size=8,
                batch_size=2,
                num_workers=0,
            )["train"]
            imagenes_vistas = sum(len(lote["id"]) for lote in cargador)

        self.assertFalse(cargador.drop_last)
        self.assertEqual(imagenes_vistas, 5)

    def test_perdida_conserva_forma_y_permite_backward(self) -> None:
        logits = torch.randn(2, 1, 8, 6, requires_grad=True)
        mascaras = torch.randint(0, 2, (2, 1, 8, 6)).float()

        perdida = PerdidaBCEDice()(logits, mascaras)
        perdida.backward()

        self.assertEqual(perdida.ndim, 0)
        self.assertTrue(torch.isfinite(perdida))
        self.assertIsNotNone(logits.grad)
        self.assertEqual(logits.grad.shape, logits.shape)
        self.assertTrue(torch.isfinite(logits.grad).all())

    def test_adaptador_acepta_salida_simulada_de_segformer(self) -> None:
        salida = SimpleNamespace(logits=torch.randn(2, 1, 2, 3))
        mascaras = torch.zeros(2, 1, 8, 6)

        adaptados = adaptar_logits(salida, mascaras)

        self.assertEqual(adaptados.shape, mascaras.shape)
        self.assertTrue(torch.isfinite(adaptados).all())

    def test_metricas_de_epoca_se_ponderan_por_imagen(self) -> None:
        datos = [
            {"image": torch.full((1, 2, 2), valor), "mask": torch.ones(1, 2, 2)}
            for valor in (20.0, -20.0, 20.0)
        ]
        cargador = DataLoader(datos, batch_size=2, shuffle=False)

        metricas = ejecutar_epoca(
            nn.Identity(),
            cargador,
            PerdidaBCEDice(),
            dispositivo="cpu",
        )

        self.assertEqual(metricas["n_imagenes"], 3)
        self.assertAlmostEqual(metricas["dice"], 2.0 / 3.0, places=6)

    def test_guarda_mejor_checkpoint_y_detiene_temprano(self) -> None:
        cargador = DataLoader(DatasetMinimo(), batch_size=2, shuffle=False)
        modelo = ModeloMinimo()

        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "mejor.pt"
            resultado = entrenar_modelo(
                modelo,
                cargador,
                cargador,
                ruta,
                epocas=5,
                paciencia=1,
                learning_rate=0.0,
                weight_decay=0.0,
                dispositivo="cpu",
            )
            metadatos = cargar_checkpoint(ruta, ModeloMinimo())

        self.assertTrue(resultado.detencion_temprana)
        self.assertEqual(len(resultado.historial), 2)
        self.assertEqual(resultado.mejor_epoca, 1)
        self.assertEqual(metadatos["epoca"], 1)
        self.assertEqual(
            list(resultado.historial.columns),
            ["epoca", "train_loss", "train_dice", "val_loss", "val_dice"],
        )

    def test_checkpoint_hace_round_trip_de_pesos(self) -> None:
        cargador = DataLoader(DatasetMinimo(2), batch_size=2, shuffle=False)
        modelo = ModeloMinimo()

        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "modelo.pt"
            entrenar_modelo(
                modelo,
                cargador,
                cargador,
                ruta,
                epocas=1,
                paciencia=1,
                learning_rate=0.01,
                dispositivo="cpu",
            )
            esperado = {clave: valor.detach().clone() for clave, valor in modelo.state_dict().items()}
            with torch.no_grad():
                for parametro in modelo.parameters():
                    parametro.add_(10.0)

            metadatos = cargar_checkpoint(ruta, modelo, dispositivo="cpu")

        self.assertEqual(metadatos["epoca"], 1)
        for clave, valor in modelo.state_dict().items():
            self.assertTrue(torch.equal(valor, esperado[clave]))


if __name__ == "__main__":
    unittest.main()
