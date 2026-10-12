"""Ordinary offline checks for CSV dashboards; no image or model execution."""

import hashlib
from io import StringIO
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
import comun


class DashboardTest(unittest.TestCase):
    def app(self, path):
        return AppTest.from_file(str(ROOT / "app" / path), default_timeout=30)

    def assert_clean(self, app):
        self.assertEqual(len(app.exception), 0, str(app.exception))

    def test_real_csv_context_and_all_pages(self):
        paths = [ROOT / "data/metrics.csv", ROOT / "data/splits.csv",
                 ROOT / "data/artefactos_entrenamiento/historial_modelos.csv",
                 ROOT / "data/artefactos_entrenamiento/experimentos_modelos.csv"]
        before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
        data = comun.cargar_datos()
        if not data["train"].empty:
            self.assertEqual(set(data["train"]["id"]), set(data["splits"]["id"]))
            self.assertEqual(len(data["train"]), 351)
        self.assertEqual(len(data["splits"]), 351)
        self.assertEqual(len(data["metricas"]), 159)
        for page in ["Inicio.py", "pages/1_Exploracion.py", "pages/3_Rendimiento.py"]:
            app = self.app(page).run()
            self.assert_clean(app)
            self.assertEqual(len(app.warning), 0)
            if "Exploracion" in page:
                self.assertEqual(app.metric[0].value, "351")
                if data["train"].empty:
                    self.assertTrue(any("train.csv" in item.value for item in app.info))
                else:
                    self.assertEqual(len(app.get("plotly_chart")), 7)
        self.assertFalse((ROOT / "app/pages/2_Prediccion.py").exists())
        self.assertEqual(len(list((ROOT / "app/pages").glob("*.py"))), 2)
        self.assertEqual(before, [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths])

    def test_performance_single_all_metric_and_organ_filters(self):
        app = self.app("pages/3_Rendimiento.py").run()
        self.assert_clean(app)
        self.assertEqual(len(app.get("plotly_chart")), 6)
        self.assertEqual(app.metric[0].value, "53")
        app.sidebar.selectbox[0].select("segformer_mit_b0").run()
        app.sidebar.multiselect[0].set_value(["lung"]).run()
        app.selectbox[0].select("iou").run()
        self.assert_clean(app)
        self.assertGreater(int(app.metric[0].value), 0)
        self.assertTrue(all(frame.value["modelo"].eq("segformer_mit_b0").all() for frame in app.dataframe))
        app.sidebar.multiselect[0].set_value([]).run()
        self.assert_clean(app)
        self.assertEqual(len(app.metric), 0)
        self.assertTrue(any("No hay métricas comunes" in item.value for item in app.info))

    def test_hide_all_performance_home_and_results_session(self):
        app = self.app("Inicio.py").run()
        self.assertEqual(len(app.metric), 3)
        app.sidebar.toggle[0].set_value(False).run()
        self.assert_clean(app)
        self.assertFalse(app.session_state["performance_visible"])
        self.assertEqual(len(app.metric), 0)
        app.switch_page("pages/3_Rendimiento.py").run()
        self.assert_clean(app)
        self.assertFalse(app.sidebar.toggle[0].value)
        self.assertEqual(len(app.get("plotly_chart")), 0)
        self.assertEqual(len(app.dataframe), 0)
        self.assertEqual(len(app.metric), 0)
        app.sidebar.toggle[0].set_value(True).run()
        self.assert_clean(app)
        self.assertEqual(len(app.get("plotly_chart")), 6)
        app.switch_page("Inicio.py").run()
        self.assert_clean(app)
        self.assertEqual(len(app.metric), 3)

    def test_pairing_missing_rows_and_conflicting_organs(self):
        frame = pd.DataFrame({"modelo": ["a", "a", "b", "b"],
                              "id": ["1", "2", "1", "2"],
                              "organ": ["lung", "kidney", "lung", "spleen"]})
        paired, excluded = comun.paired_metrics(frame, ["a", "b"])
        self.assertEqual(set(paired["id"]), {"1"})
        self.assertEqual(excluded, 2)
        paired, excluded = comun.paired_metrics(frame, ["a", "missing"])
        self.assertTrue(paired.empty)
        self.assertEqual(excluded, 2)
        paired, excluded = comun.paired_metrics(frame, ["a"])
        self.assertEqual(len(paired), 2)
        self.assertEqual(excluded, 0)

    def test_available_metadata_filters_and_rle_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            pd.DataFrame({"id": [1, 2], "organ": ["lung", "kidney"], "split": ["train", "val"]}).to_csv(data / "splits.csv", index=False)
            pd.DataFrame({"id": [1, 2], "organ": ["lung", "kidney"], "age": [30, 60],
                          "sex": ["Female", "Male"], "data_source": ["HPA", "HuBMAP"],
                          "img_width": [10, 20], "img_height": [10, 20], "pixel_size": [.4, .5],
                          "rle": ["1 10 21 10", ""]}).to_csv(data / "train.csv", index=False)
            with patch.object(comun, "DATA", data), patch.object(comun, "ARTEFACTOS", data):
                loaded = comun.cargar_datos()
                self.assertEqual(list(loaded["train"]["proporcion_ftu"]), [.2, 0.])
                app = self.app("pages/1_Exploracion.py").run()
                self.assert_clean(app)
                self.assertEqual(len(app.get("plotly_chart")), 7)
                self.assertNotIn("rle", app.dataframe[0].value.columns)
                app.sidebar.multiselect[0].set_value(["lung"]).run()
                self.assert_clean(app)
                self.assertEqual(app.metric[0].value, "1")
                app.sidebar.multiselect[2].set_value([]).run()
                self.assert_clean(app)
                self.assertEqual(len(app.get("plotly_chart")), 0)
                self.assertEqual(len(app.metric), 0)

    def test_missing_empty_malformed_assets_never_fabricate(self):
        scenarios = [None, "", "unexpected\n1\n", "modelo,id,organ,dice,iou\nunet_resnet34,,lung,invalid,.2\n"]
        for content in scenarios:
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                data = Path(directory)
                if content is not None:
                    for filename in ["splits.csv", "train.csv", "metrics.csv", "historial_modelos.csv", "experimentos_modelos.csv"]:
                        (data / filename).write_text(content, encoding="utf-8")
                with patch.object(comun, "DATA", data), patch.object(comun, "ARTEFACTOS", data):
                    loaded = comun.cargar_datos()
                    self.assertEqual(len(loaded["issues"]), 5)
                    for page in ["Inicio.py", "pages/1_Exploracion.py", "pages/3_Rendimiento.py"]:
                        app = self.app(page).run()
                        self.assert_clean(app)
                        self.assertEqual(len(app.metric), 0)
                        self.assertEqual(len(app.get("plotly_chart")), 0)

    def test_numeric_ranges_and_duplicate_rows_rejected(self):
        frame = pd.DataFrame({"modelo": ["unet_resnet34"], "id": [1], "organ": ["lung"], "dice": [.5], "iou": [.4]})
        for variant in [frame.assign(dice=1.1), frame.assign(iou=float("inf")),
                        frame.assign(dice=None), pd.concat([frame, frame]), frame.assign(modelo="unknown")]:
            with self.subTest(variant=variant), tempfile.TemporaryDirectory() as directory:
                data = Path(directory)
                variant.to_csv(data / "metrics.csv", index=False)
                with patch.object(comun, "DATA", data), patch.object(comun, "ARTEFACTOS", data):
                    self.assertTrue(comun.cargar_datos()["metricas"].empty)

    def test_invalid_optional_train_does_not_block_results(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            for rle in ["1", "99 5", "1 -2", "1 10 5 2"]:
                pd.DataFrame({"id": [1], "organ": ["lung"], "img_width": [10],
                              "img_height": [10], "rle": [rle]}).to_csv(data / "train.csv", index=False)
                with patch.object(comun, "DATA", data):
                    loaded = comun.cargar_datos()
                    self.assertTrue(loaded["train"].empty)
                    self.assertFalse(loaded["historial"].empty)
                    app = self.app("pages/3_Rendimiento.py").run()
                    self.assert_clean(app)
                    self.assertEqual(len(app.get("plotly_chart")), 2)

    def test_rle_overflow_and_malformed_bounds_rejected_in_memory(self):
        original_reader = pd.read_csv
        invalid = [
            (10, 10, "9223372036854775807 2"),
            (10, 10, "1 9223372036854775807"),
            (10, 10, "9223372036854775808 1"),
            (10, 10, f"1 {10 ** 100}"),
            (10, 10, "100 2"),
            (10, 10, "101 1"),
            (10, 10, "1 10 10 1"),
            (10, 10, "1 1 1 1"),
            (10, 10, "1"),
            (10, 10, "1 -1"),
            (10, 10, "0 1"),
            (10, 10, "1 0"),
            (10, 10, "1 1.5"),
            (10, 10, "abc 2"),
            (10.5, 10, "1 1"),
            (0, 10, ""),
            ("1e309", 10, "1 1"),
            (10 ** 100, 10, "1 1"),
        ]
        for height, width, rle in invalid:
            with self.subTest(height=height, width=width, rle=rle):
                fixture = f"id,organ,img_height,img_width,rle\n62,kidney,{height},{width},{rle}\n"

                def reader(path, *args, **kwargs):
                    if path == comun.DATA / "train.csv":
                        return original_reader(StringIO(fixture))
                    return original_reader(path, *args, **kwargs)

                with patch.object(comun.pd, "read_csv", side_effect=reader):
                    loaded = comun.cargar_datos()
                self.assertTrue(loaded["train"].empty)
                self.assertTrue(any(issue.startswith("train.csv:") for issue in loaded["issues"]))
                self.assertEqual(len(loaded["metricas"]), 159)

    def test_rle_exact_end_large_area_and_sum_do_not_overflow(self):
        valid = [
            (10, 10, "", 0.),
            (10, 10, "100 1", .01),
            (10, 10, "1 100", 1.),
            (10, 10, "1 50 51 50", 1.),
            (3_100_000_000, 3_100_000_000, "1 9223372036854775807",
             9223372036854775807 / (3_100_000_000 ** 2)),
            (9223372036854775807, 2,
             "1 9223372036854775806 9223372036854775807 9223372036854775807",
             18446744073709551613 / 18446744073709551614),
        ]
        for height, width, rle, expected in valid:
            with self.subTest(height=height, width=width, rle=rle):
                row = pd.Series({"img_height": height, "img_width": width, "rle": rle})
                coverage = comun._proporcion_ftu(row)
                self.assertEqual(coverage, expected)
                self.assertGreaterEqual(coverage, 0.)
                self.assertLessEqual(coverage, 1.)

    def test_partial_metrics_disclose_exclusions_and_use_common_ids(self):
        loaded = comun.cargar_datos()
        loaded["metricas"] = loaded["metricas"].iloc[1:]
        with patch.object(comun, "cargar_datos", return_value=loaded):
            app = self.app("pages/3_Rendimiento.py").run()
            self.assert_clean(app)
            self.assertEqual(app.metric[0].value, "52")
            self.assertEqual(len(app.warning), 0)
            self.assertTrue(any("sin pareja" in item.value for item in app.caption))
            app = self.app("Inicio.py").run()
            self.assert_clean(app)
            self.assertEqual(len(app.warning), 0)
            self.assertTrue(any("sin pareja" in item.value for item in app.caption))

    def test_optional_history_and_experiments_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            pd.DataFrame({"modelo": ["unet_resnet34"], "epoca": [1.5], "train_loss": [.2],
                          "val_loss": [.3], "train_dice": [.4], "val_dice": [.5]}).to_csv(data / "historial_modelos.csv", index=False)
            pd.DataFrame({"modelo": ["unet_resnet34"], "mejor_epoca": [1],
                          "mejor_val_dice": [2]}).to_csv(data / "experimentos_modelos.csv", index=False)
            with patch.object(comun, "ARTEFACTOS", data):
                loaded = comun.cargar_datos()
                self.assertTrue(loaded["historial"].empty)
                self.assertTrue(loaded["experimentos"].empty)
                app = self.app("pages/3_Rendimiento.py").run()
                self.assert_clean(app)
                self.assertEqual(len(app.get("plotly_chart")), 4)
                self.assertEqual(len(app.warning), 0)
                for filename in ("historial_modelos.csv", "experimentos_modelos.csv"):
                    self.assertTrue(any(filename in item.value for item in app.info))


if __name__ == "__main__":
    unittest.main()
