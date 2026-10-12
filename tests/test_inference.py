"""Functional FD2 checks using generated uploads and local synthetic weights."""

from io import BytesIO
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import cv2
import numpy as np
from PIL import Image
import streamlit as st
from streamlit.testing.v1 import AppTest
import tifffile
import torch
from torch import nn

from src import inference as inf
from src import preprocess as pp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import comun


def png(array):
    stream = BytesIO()
    Image.fromarray(array).save(stream, format="PNG")
    return stream.getvalue()


class BinaryModel(nn.Module):
    def forward(self, tensor):
        assert not self.training
        assert torch.is_inference_mode_enabled()
        return SimpleNamespace(logits=torch.zeros(1, 1, 96, 96))


class InferenceTest(unittest.TestCase):
    def test_cache_and_validation_equivalence(self):
        rgb = np.random.default_rng(7).integers(0, 256, (533, 719, 3), dtype=np.uint8)
        result = inf.prepare_tensor(inf.decode_upload(png(rgb)))
        # Independent cache round trip, as preparar_cache/HubmapDataset perform it.
        cache = cv2.resize(rgb, (384, 384), interpolation=cv2.INTER_AREA)
        success, encoded = cv2.imencode(".png", cv2.cvtColor(cache, cv2.COLOR_RGB2BGR))
        self.assertTrue(success)
        decoded = cv2.cvtColor(cv2.imdecode(encoded, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        expected = pp.transformaciones("val", 384)(image=decoded)["image"]
        np.testing.assert_array_equal(result.numpy()[0], expected.transpose(2, 0, 1))
        self.assertEqual(result.shape, (1, 3, 384, 384))
        self.assertEqual(result.dtype, torch.float32)

    def test_rgb_jpeg_grayscale_alpha_and_uint16(self):
        rgb = np.full((20, 30, 3), [20, 90, 180], dtype=np.uint8)
        jpeg = BytesIO()
        Image.fromarray(rgb).save(jpeg, format="JPEG")
        self.assertEqual(inf.decode_upload(jpeg.getvalue()).shape, rgb.shape)
        gray = np.arange(600, dtype=np.uint16).reshape(20, 30)
        for content in (png(gray), self.tiff(gray)):
            decoded = inf.decode_upload(content)
            np.testing.assert_array_equal(decoded, pp.a_rgb_uint8(gray))
        np.testing.assert_array_equal(
            inf.decode_upload(png(rgb[..., 0])), pp.a_rgb_uint8(rgb[..., 0]),
        )
        rgba = np.concatenate([rgb, np.zeros((20, 30, 1), dtype=np.uint8)], axis=2)
        np.testing.assert_array_equal(inf.decode_upload(png(rgba)), rgb)
        np.testing.assert_array_equal(
            inf.decode_upload(self.tiff(rgb.astype(np.uint16))),
            pp.a_rgb_uint8(rgb.astype(np.uint16)),
        )
        np.testing.assert_array_equal(
            inf.decode_upload(self.tiff(np.full((20, 30), 1000, dtype=np.uint16))),
            np.zeros_like(rgb),
        )

    def test_planar_tiff_and_unsupported_color_depth(self):
        rgb = np.random.default_rng(3).integers(0, 65536, (20, 30, 3), dtype=np.uint16)
        content = self.tiff(rgb.transpose(2, 0, 1), photometric="rgb", planarconfig="separate")
        np.testing.assert_array_equal(inf.decode_upload(content), pp.a_rgb_uint8(rgb))
        valid, encoded = cv2.imencode(".png", rgb[..., ::-1])
        self.assertTrue(valid)
        with self.assertRaisesRegex(inf.InferenceError, "PNG RGB de 16 bits"):
            inf.decode_upload(encoded.tobytes())
        with (
            patch.object(inf, "MAX_PIXELS", 500),
            patch.object(tifffile.TiffPageSeries, "asarray", side_effect=AssertionError("decode too early")),
            self.assertRaises(inf.InferenceError),
        ):
            inf.decode_upload(content)

    @staticmethod
    def tiff(array, **kwargs):
        stream = BytesIO()
        tifffile.imwrite(stream, array, **kwargs)
        return stream.getvalue()

    def test_invalid_uploads_and_budgets(self):
        for content in (b"", b"not an image", png(np.zeros((1, 10), dtype=np.uint8)),
                        self.tiff(np.zeros((20, 30), dtype=np.float32)),
                        self.tiff(np.zeros((2, 20, 30), dtype=np.uint8), photometric="minisblack")):
            with self.subTest(size=len(content)), self.assertRaises(inf.InferenceError):
                inf.decode_upload(content)
        content = png(np.zeros((20, 30), dtype=np.uint8))
        with patch.object(inf, "MAX_UPLOAD_BYTES", len(content) - 1), self.assertRaises(inf.InferenceError):
            inf.decode_upload(content)
        with (
            patch.object(inf, "MAX_PIXELS", 500),
            patch.object(Image.Image, "load", side_effect=AssertionError("decode too early")),
            self.assertRaisesRegex(inf.InferenceError, "9 millones"),
        ):
            inf.decode_upload(content)

    def test_binary_alignment_threshold_and_original_size(self):
        rgb = np.full((29, 43, 3), 60, dtype=np.uint8)
        model = BinaryModel()
        result = inf.predict(model, rgb)
        self.assertEqual(result.mask.shape, (29, 43))
        self.assertEqual(result.overlay.shape, rgb.shape)
        np.testing.assert_array_equal(result.mask, np.ones((29, 43), dtype=np.uint8))
        np.testing.assert_array_equal(result.probabilities, np.full((384, 384), .5))
        self.assertEqual(result.coverage_percent, 100)
        self.assertGreaterEqual(result.seconds, 0)
        self.assertFalse(model.training)

    def test_logit_interpolation_precedes_sigmoid_and_mask_restore(self):
        rgb = np.zeros((29, 43, 3), dtype=np.uint8)
        logits = torch.tensor([[[[-4., 2.], [1., -3.]]]])
        model = BinaryModel()
        with patch.object(model, "forward", return_value=logits):
            result = inf.predict(model, rgb)
        expected = torch.sigmoid(torch.nn.functional.interpolate(
            logits, size=(384, 384), mode="bilinear", align_corners=False,
        ))[0, 0].numpy()
        np.testing.assert_array_equal(result.probabilities, expected)
        np.testing.assert_array_equal(result.mask, cv2.resize(
            (expected >= .5).astype(np.uint8), (43, 29), interpolation=cv2.INTER_NEAREST,
        ))

    def test_invalid_output_shapes_and_nonfinite(self):
        rgb = np.zeros((20, 30, 3), dtype=np.uint8)
        for output in (torch.zeros(1, 5, 96, 96), torch.zeros(2, 1, 96, 96),
                       torch.full((1, 1, 96, 96), float("nan")), object()):
            model = BinaryModel()
            with patch.object(model, "forward", return_value=output), self.assertRaises((ValueError, TypeError)):
                inf.predict(model, rgb)

    def test_safe_strict_checkpoint_and_missing_weights(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unet_resnet34.pt"
            self.assertEqual(inf.available_checkpoints(Path(directory)), {})
            with self.assertRaisesRegex(inf.InferenceError, "Falta"):
                inf.load_model("unet_resnet34", path)
            model = nn.Conv2d(3, 1, 1)
            torch.save({"formato": 1, "modelo": model.state_dict(), "epoca": 1, "val_dice": .1}, path)
            original_load = torch.load
            with (
                patch("src.evaluation.crear_modelo", return_value=nn.Conv2d(3, 1, 1)) as factory,
                patch("src.training.torch.load", wraps=original_load) as loader,
            ):
                loaded = inf.load_model("unet_resnet34", path)
                factory.assert_called_once_with("unet_resnet34", pesos_preentrenados=False)
                self.assertTrue(loader.call_args.kwargs["weights_only"])
                self.assertEqual(str(loader.call_args.kwargs["map_location"]), "cpu")
                self.assertFalse(loaded.training)
            torch.save({"formato": 1, "modelo": {}, "epoca": 1, "val_dice": .1}, path)
            with (
                patch("src.evaluation.crear_modelo", return_value=nn.Conv2d(3, 1, 1)),
                self.assertRaisesRegex(inf.InferenceError, "incompatible"),
            ):
                inf.load_model("unet_resnet34", path)


class PredictionPageTest(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(ROOT / "app/pages/2_Prediccion.py"), default_timeout=30)

    def test_missing_checkpoints_no_fake_prediction(self):
        with patch.object(inf, "available_checkpoints", return_value={}):
            app = self.app().run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("bloqueada" in message.value for message in app.warning))
        self.assertEqual(len(app.button), 0)
        self.assertEqual(len(app.metric), 0)

    def test_available_without_upload(self):
        with patch.object(inf, "available_checkpoints", return_value={"segformer_mit_b0": Path("synthetic.pt")}):
            app = self.app().run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("Suba una imagen" in message.value for message in app.info))
        self.assertEqual(len(app.metric), 0)

    def test_single_and_all_available_models(self):
        available = {name: Path(f"{name}.pt") for name in comun.NOMBRES_COMPLETOS}
        upload = SimpleNamespace(getvalue=lambda: png(np.full((20, 30, 3), 80, dtype=np.uint8)))
        with (
            patch.object(inf, "available_checkpoints", return_value=available),
            patch.object(st, "file_uploader", return_value=upload),
            patch.object(inf, "load_model", side_effect=lambda *args: BinaryModel()) as loader,
        ):
            app = self.app().run()
            app.button[0].click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.metric), 2)
            self.assertEqual(loader.call_count, 1)
            app.selectbox[1].select("all").run()
            app.button[0].click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.metric), 6)
            self.assertEqual(loader.call_count, 4)

    def test_bad_upload_and_individual_model_failure(self):
        available = {name: Path(f"{name}.pt") for name in comun.NOMBRES_COMPLETOS}
        upload = SimpleNamespace(getvalue=lambda: b"invalid")
        with (
            patch.object(inf, "available_checkpoints", return_value=available),
            patch.object(st, "file_uploader", return_value=upload),
        ):
            app = self.app().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.error), 1)
            self.assertEqual(len(app.metric), 0)
        upload = SimpleNamespace(getvalue=lambda: png(np.zeros((20, 30, 3), dtype=np.uint8)))

        def partial_load(name, path):
            if name == "unet_resnet34":
                raise inf.InferenceError("Checkpoint incompatible; no se generó una predicción.")
            return BinaryModel()

        with (
            patch.object(inf, "available_checkpoints", return_value=available),
            patch.object(st, "file_uploader", return_value=upload),
            patch.object(inf, "load_model", side_effect=partial_load),
        ):
            app = self.app().run()
            app.selectbox[1].select("all").run()
            app.button[0].click().run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.error), 1)
            self.assertEqual(len(app.metric), 4)


if __name__ == "__main__":
    unittest.main()
