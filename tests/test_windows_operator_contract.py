"""Contratos estáticos de la operación segura del handoff en Windows."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]


class ContratosOperadorWindowsTest(unittest.TestCase):
    def test_settings_y_hook_tienen_forma_y_bloqueos_requeridos(self) -> None:
        settings = json.loads((RAIZ / ".claude/settings.json").read_text(encoding="utf-8"))
        entrada = settings["hooks"]["PreToolUse"][0]
        self.assertEqual(entrada["matcher"], "Bash")
        self.assertIn("guard-training.ps1", entrada["hooks"][0]["command"])
        hook = (RAIZ / ".claude/hooks/guard-training.ps1").read_text(encoding="utf-8")
        for contrato in ("convertfrom-json", "exit 2", "wsl", "/mnt/", "code", "jupyter", "nbconvert", "train_windows", "windows_training"):
            self.assertIn(contrato, hook.lower())
        self.assertIn("(Verify|Preflight)", hook)
        self.assertIn("-Stage\\s+Train", hook)
        self.assertIn("ejecutar manualmente", hook)

    def test_harness_encadena_estado_y_huella(self) -> None:
        harness = (RAIZ / "scripts/windows_training.ps1").read_text(encoding="utf-8")
        for contrato in (
            "Set-StrictMode", "$ErrorActionPreference = \"Stop\"", "uv sync --frozen",
            "unittest discover", "Get-Fingerprint", "Get-Head", "evidence_sha256",
            '"pyproject.toml"', '"scripts/windows_training.ps1"',
            "Falta evidencia local", "evidencia quedó obsoleta", 'Read-State "verify"',
            'Read-State "preflight"', 'Write-State "train" $Evidence $PreflightState',
            "Read-Host", "ENTRENAR",
        ):
            self.assertIn(contrato, harness)

    def test_instrucciones_skill_y_guia_autorizan_reparacion_acotada(self) -> None:
        artefactos = {
            "CLAUDE.md": (RAIZ / "CLAUDE.md").read_text(encoding="utf-8"),
            "skill": (RAIZ / ".claude/skills/windows-training-operator/SKILL.md").read_text(encoding="utf-8"),
            "guía": (RAIZ / "docs/ejecucion_entrenamiento_windows.md").read_text(encoding="utf-8"),
        }
        for nombre, contenido in artefactos.items():
            with self.subTest(artefacto=nombre):
                for contrato in (
                    "script", "prueba", "skill", "configuración", "contrato documentado",
                    "autoridad", "diagnosticar", "repar", "Verify", "Preflight",
                ):
                    self.assertIn(contrato, contenido)
                self.assertIn("Verify` completo", contenido)
                self.assertIn("hiperparámetros conservadores", contenido)
                self.assertIn("fabrique evidencia", contenido)
                self.assertIn("amplíe permisos", contenido)
                self.assertIn("máquina", contenido)
                self.assertIn("red", contenido)
                self.assertIn("controlador", contenido)
                self.assertIn("disco", contenido)

    def test_contratos_de_instrucciones_skill_y_comandos(self) -> None:
        instrucciones = (RAIZ / "CLAUDE.md").read_text(encoding="utf-8")
        for texto in ("windows-training-operator", "Verify", "Preflight", "Train", "WSL", "test", "push"):
            self.assertIn(texto, instrucciones)
        self.assertIn("no invoque Train mediante Bash", instrucciones)
        self.assertIn("ejecute manualmente", instrucciones)
        skill = (RAIZ / ".claude/skills/windows-training-operator/SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill.startswith("---\nname: windows-training-operator\n"))
        self.assertLess(len(skill.splitlines()), 500)
        self.assertIn("no ejecute Train con Bash", skill)
        comandos = (RAIZ / "comandos_windows.txt").read_text(encoding="utf-8").splitlines()
        self.assertTrue(all(line.startswith("#") or line.startswith("$") or line.startswith("Set-Location") or line.startswith("claude") or line.startswith("powershell.exe") or not line for line in comandos))
        self.assertEqual(sum("-Stage Verify" in line for line in comandos), 1)
        self.assertEqual(sum("-Stage Preflight" in line for line in comandos), 1)
        self.assertEqual(sum("-Stage Train" in line for line in comandos), 1)
        ejecutables = [line for line in comandos if line and not line.startswith("#")]
        self.assertFalse(any("-Stage Verify" in line or "-Stage Preflight" in line for line in ejecutables))
        self.assertIn("-Stage Train", ejecutables[-1])

    def test_readme_conserva_configuracion_y_esquemas_detallados(self) -> None:
        readme = (RAIZ / "README.md").read_text(encoding="utf-8")
        for contrato in (
            "384 × 384 px", "batch físico", "acumulación de gradientes",
            "checkpoints/<modelo>.pt", "historial_modelos.csv",
            "experimentos_modelos.csv", "2.7 Entrega para la Persona 2",
            "ejecucion_entrenamiento_windows.md",
        ):
            self.assertIn(contrato, readme)


if __name__ == "__main__":
    unittest.main()
