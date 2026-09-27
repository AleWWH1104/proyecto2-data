"""Pruebas offline del runner de entrenamiento para Windows."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from scripts import train_windows as runner


RAIZ = Path(__file__).resolve().parents[1]


def sistema_valido(**cambios: object) -> runner.InformacionSistema:
    valores = {
        "sistema": "Windows",
        "version": "11",
        "es_wsl": False,
        "cuda_disponible": True,
        "gpu": "NVIDIA GeForce RTX 4050 Laptop GPU",
        "vram_total_bytes": 6 * 1024**3,
        "vram_libre_bytes": 5 * 1024**3,
    }
    valores.update(cambios)
    return runner.InformacionSistema(**valores)


def crear_datos_validos(raiz: Path) -> None:
    datos = raiz / "data"
    imagenes = datos / "train_images"
    imagenes.mkdir(parents=True)
    ids = list(range(1000, 1351))
    pd.DataFrame(
        {
            "id": ids,
            "organ": ["kidney"] * 351,
            "rle": ["1 1"] * 351,
            "pixel_size": [0.4] * 351,
        }
    ).to_csv(datos / "train.csv", index=False)
    splits = ["train"] * 245 + ["val"] * 53 + ["test"] * 53
    pd.DataFrame({"id": ids, "organ": ["kidney"] * 351, "split": splits}).to_csv(
        datos / "splits.csv", index=False
    )
    for identificador in ids:
        (imagenes / f"{identificador}.tiff").touch()


class ValidacionEntornoTest(unittest.TestCase):
    def test_acepta_las_dos_gpu_objetivo(self) -> None:
        runner.validar_entorno(
            sistema_valido(vram_total_bytes=int(5.75 * 1024**3)),
            Path(r"C:\proyecto"),
        )
        runner.validar_entorno(
            sistema_valido(
                gpu="NVIDIA GeForce RTX 4060 Laptop GPU",
                vram_total_bytes=8 * 1024**3,
                vram_libre_bytes=6 * 1024**3,
            ),
            Path(r"C:\proyecto"),
        )

    def test_rechaza_linux_wsl_gpu_y_memoria_invalidos(self) -> None:
        casos = [
            (sistema_valido(sistema="Linux"), Path("/home/proyecto"), "Windows nativo"),
            (sistema_valido(es_wsl=True), Path(r"C:\proyecto"), "WSL"),
            (sistema_valido(), Path("/mnt/c/proyecto"), "WSL"),
            (sistema_valido(cuda_disponible=False), Path(r"C:\proyecto"), "CUDA"),
            (sistema_valido(gpu="NVIDIA RTX 3090"), Path(r"C:\proyecto"), "GPU no admitida"),
            (sistema_valido(vram_total_bytes=int(5.4 * 1024**3)), Path(r"C:\proyecto"), "VRAM insuficiente"),
            (sistema_valido(vram_libre_bytes=3 * 1024**3), Path(r"C:\proyecto"), "libre insuficiente"),
        ]
        for info, ruta, mensaje in casos:
            with self.subTest(mensaje=mensaje):
                with self.assertRaisesRegex(runner.ErrorHandoff, mensaje):
                    runner.validar_entorno(info, ruta)

    def test_override_de_prueba_no_finge_cuda_ni_permite_wsl(self) -> None:
        runner.validar_entorno(
            sistema_valido(sistema="Linux"),
            Path("/home/proyecto"),
            permitir_no_windows_en_pruebas=True,
        )
        with self.assertRaisesRegex(runner.ErrorHandoff, "WSL"):
            runner.validar_entorno(
                sistema_valido(sistema="Linux", es_wsl=True),
                Path("/home/proyecto"),
                permitir_no_windows_en_pruebas=True,
            )


class ValidacionDatosTest(unittest.TestCase):
    def test_valida_351_imagenes_y_splits_245_53_53(self) -> None:
        with tempfile.TemporaryDirectory() as directorio:
            raiz = Path(directorio)
            crear_datos_validos(raiz)
            train, splits = runner.validar_datos(raiz)
        self.assertEqual(len(train), 351)
        self.assertEqual(splits["split"].value_counts().to_dict(), runner.CONTEOS_ESPERADOS)

    def test_rechaza_conteo_incorrecto_sin_abrir_imagenes(self) -> None:
        with tempfile.TemporaryDirectory() as directorio:
            raiz = Path(directorio)
            crear_datos_validos(raiz)
            splits = pd.read_csv(raiz / "data" / "splits.csv")
            splits.loc[0, "split"] = "val"
            splits.to_csv(raiz / "data" / "splits.csv", index=False)
            with self.assertRaisesRegex(runner.ErrorHandoff, "Conteos de splits"):
                runner.validar_datos(raiz)

    def test_verify_inyectado_no_consulta_torch_cuda_red_o_entrenamiento(self) -> None:
        with tempfile.TemporaryDirectory() as directorio:
            raiz = Path(directorio)
            crear_datos_validos(raiz)
            with patch.object(
                runner,
                "obtener_informacion_sistema",
                side_effect=AssertionError("No debe consultar CUDA"),
            ):
                resultado = runner.verificar(raiz, sistema_valido())
        self.assertEqual(resultado["estado"], "correcto")
        self.assertEqual(resultado["datos"], {"total": 351, "train": 245, "val": 53, "test": 53})


class ContratosRunnerTest(unittest.TestCase):
    def test_runner_preserva_esquemas_modelos_preentrenados_y_no_itera_test(self) -> None:
        self.assertEqual(
            runner.COLUMNAS_HISTORIAL,
            ["modelo", "epoca", "train_loss", "train_dice", "val_loss", "val_dice"],
        )
        fuente = (RAIZ / "scripts/train_windows.py").read_text(encoding="utf-8")
        self.assertNotIn('cargadores["test"]', fuente)
        self.assertIn("pesos_preentrenados=True", fuente)
        self.assertIn("torch.cuda.empty_cache()", fuente)
        self.assertNotIn("test", runner.entrenar.__code__.co_names)


if __name__ == "__main__":
    unittest.main()
