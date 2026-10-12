"""Offline contracts for local installs and the existing Windows CUDA lock."""

import tomllib
import unittest
from pathlib import Path

from packaging.markers import Marker


ROOT = Path(__file__).resolve().parents[1]
PYPI = "https://pypi.org/simple"
CUDA_INDEX = "https://download.pytorch.org/whl/cu130"


class PlatformDependenciesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project = tomllib.loads((ROOT / "pyproject.toml").read_text())
        cls.lock = tomllib.loads((ROOT / "uv.lock").read_text())

    def test_cuda_source_is_explicit_and_windows_only(self) -> None:
        uv = self.project["tool"]["uv"]
        index = next(item for item in uv["index"] if item["name"] == "pytorch-cu130")
        self.assertEqual(index["url"], CUDA_INDEX)
        self.assertTrue(index["explicit"])
        sources = uv["sources"]["torch"]
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["index"], "pytorch-cu130")
        marker = Marker(sources[0]["marker"])
        for platform in ("win32", "darwin", "linux"):
            with self.subTest(platform=platform):
                self.assertEqual(marker.evaluate({"sys_platform": platform}), platform == "win32")

    def test_lock_routes_torch_consistently_for_direct_and_transitive_users(self) -> None:
        users = ("proyecto2-data", "segmentation-models-pytorch", "timm", "torchvision")
        for name in users:
            package = next(item for item in self.lock["package"] if item["name"] == name)
            dependencies = [item for item in package["dependencies"] if item["name"] == "torch"]
            for platform in ("win32", "darwin", "linux"):
                for python in ("3.11.17", "3.12.15"):
                    with self.subTest(package=name, platform=platform, python=python):
                        active = [
                            item for item in dependencies
                            if Marker(item.get("marker", "python_version >= '3.11'")).evaluate(
                                {"sys_platform": platform, "python_full_version": python,
                                 "python_version": ".".join(python.split(".")[:2])}
                            )
                        ]
                        self.assertEqual(len(active), 1)
                        expected = CUDA_INDEX if platform == "win32" else PYPI
                        self.assertEqual(active[0]["source"]["registry"], expected)
                        version = "2.14.1+cu130" if platform == "win32" else "2.14.1"
                        self.assertEqual(active[0]["version"], version)

    def test_windows_torch_version_and_cp311_wheel_remain_unchanged(self) -> None:
        package = next(
            item for item in self.lock["package"]
            if item["name"] == "torch" and item["source"]["registry"] == CUDA_INDEX
        )
        self.assertEqual(package["version"], "2.14.1+cu130")
        wheel = next(item for item in package["wheels"] if "cp311-cp311-win_amd64" in item["url"])
        self.assertEqual(
            wheel["hash"],
            "sha256:e98711737150b5a6451cbbfdb425abd5d1bea77f4a1a5d29c48d5ec41cd54949",
        )

    def test_mac_torch_has_a_hashed_apple_silicon_wheel(self) -> None:
        package = next(
            item for item in self.lock["package"]
            if item["name"] == "torch" and item["source"]["registry"] == PYPI
        )
        wheels = [item for item in package["wheels"] if "cp311-cp311-macosx_14_0_arm64" in item["url"]]
        self.assertEqual(len(wheels), 1)
        self.assertTrue(wheels[0]["hash"].startswith("sha256:"))

    def test_torchvision_preserves_the_existing_pypi_version_and_windows_wheel(self) -> None:
        packages = [item for item in self.lock["package"] if item["name"] == "torchvision"]
        self.assertEqual(len(packages), 1)
        self.assertEqual(packages[0]["version"], "0.29.1")
        self.assertEqual(packages[0]["source"]["registry"], PYPI)
        wheel = next(item for item in packages[0]["wheels"] if "cp311-cp311-win_amd64" in item["url"])
        self.assertEqual(
            wheel["hash"],
            "sha256:3ffbf206311067faa5d8d7c70237d26df7b74012bcaa1bc6782a4eb615394925",
        )

    def test_torchvision_cpu_operator_loads_with_torch(self) -> None:
        import torch
        from torchvision.ops import nms

        boxes = torch.tensor([[0.0, 0.0, 2.0, 2.0], [0.0, 0.0, 2.0, 2.0]])
        scores = torch.tensor([0.9, 0.8])
        self.assertEqual(nms(boxes, scores, 0.5).tolist(), [0])


if __name__ == "__main__":
    unittest.main()
