"""Security and quality gate with one integrated final decision."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def stage(name: str, checks: list[str]) -> bool:
    print(f"\n[ETAPA] {name}")
    if checks:
        for check in checks:
            print(f"  [HALLAZGO] {check}")
        print(f"  [BLOQUEA] {name}: umbral incumplido")
        return False
    print("  [OK] Sin hallazgos sobre el umbral definido")
    return True


def secret_scan(root: Path) -> list[str]:
    findings = []
    assignment = re.compile(r"(?:AWS_SECRET_ACCESS_KEY|AWS_ACCESS_KEY_ID|DB_PASSWORD|FLASK_SECRET_KEY)\s*=\s*[^\s#]+", re.I)
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        if any(part in {".git", ".venv", "venv", "node_modules", "__pycache__"} for part in path.parts):
            continue
        if path.name == ".env" or path.name == "terraform.tfvars":
            # Local development configuration is intentionally ignored by Git.
            # A tracked .env or terraform.tfvars is still caught by the repository hygiene check.
            if path.is_relative_to(ROOT):
                tracked = subprocess.run(
                    ["git", "ls-files", "--error-unmatch", str(path.relative_to(ROOT))],
                    cwd=ROOT,
                    capture_output=True,
                )
                if tracked.returncode:
                    continue
        if path.name == "run_pipeline.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            if ".example" in path.name and "replace-with" in line:
                continue
            if assignment.search(line):
                label = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name
                findings.append(f"{label}:{line_number}: asignación de secreto")
            if "BEGIN PRIVATE KEY" in line:
                label = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name
                findings.append(f"{label}:{line_number}: llave privada")
    return findings


def iac_scan() -> list[str]:
    text = (ROOT / "infra" / "main.tf").read_text(encoding="utf-8")
    required = {
        "bloqueo de acceso público S3": "aws_s3_bucket_public_access_block",
        "cifrado S3": "sse_algorithm = \"AES256\"",
        "cifrado RDS": "storage_encrypted       = true",
        "RDS privado": "publicly_accessible     = false",
    }
    return [f"{label}: falta '{needle}'" for label, needle in required.items() if needle not in text]


def docker_scan() -> list[str]:
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    checks = {
        "imagen base versionada": re.search(r"^FROM\s+\S+:\S+", text, re.M),
        "usuario no root": re.search(r"^USER\s+appuser", text, re.M),
        "healthcheck": re.search(r"^HEALTHCHECK\s+", text, re.M),
    }
    return [f"Dockerfile: falta {label}" for label, found in checks.items() if not found]


def tests() -> list[str]:
    compile_result = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "app"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if compile_result.returncode:
        return [compile_result.stdout or compile_result.stderr or "compileall falló"]
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "app")}
    unit_result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "app/tests", "-p", "test_*.py"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
    )
    if unit_result.returncode:
        return [unit_result.stdout[-1200:] or unit_result.stderr[-1200:] or "pruebas unitarias fallaron"]
    return []


def bandit_scan() -> list[str]:
    output = ROOT / "reportes" / "bandit.json"
    with tempfile.TemporaryDirectory(prefix="dangoko-bandit-") as temp_dir:
        fresh = Path(temp_dir) / "bandit.json"
        result = subprocess.run(
            [sys.executable, "-m", "bandit", "-r", "app/backend", "app/notifications_service.py", "-f", "json", "-o", str(fresh), "-q"],
            cwd=ROOT, capture_output=True, text=True,
        )
        if not fresh.is_file():
            return ["Bandit no generó un reporte; instala pipeline/requirements-tools.txt. " + result.stderr[-300:]]
        try:
            report = json.loads(fresh.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            return [f"El reporte de Bandit no es JSON válido: {error}"]
        if result.returncode not in (0, 1) or report.get("errors"):
            return ["Bandit no pudo completar el análisis: " + str(report.get("errors") or result.stderr[-300:])]
        shutil.copyfile(fresh, output)
    findings = report.get("results", [])
    print(f"  Bandit: {len(findings)} avisos; reporte: reportes/bandit.json")
    return [
        f"{issue['filename']}:{issue['line_number']} {issue['test_id']} {issue['issue_severity']}: {issue['issue_text']}"
        for issue in findings if issue.get("issue_severity") == "HIGH"
    ]


def dependency_scan() -> list[str]:
    output = ROOT / "reportes" / "pip_audit.json"
    with tempfile.TemporaryDirectory(prefix="dangoko-audit-") as temp_dir:
        fresh = Path(temp_dir) / "pip_audit.json"
        result = subprocess.run(
            [sys.executable, "-m", "pip_audit", "-r", "app/requirements.txt", "--format", "json", "--desc", "off", "--progress-spinner", "off", "-o", str(fresh)],
            cwd=ROOT, capture_output=True, text=True,
        )
        if not fresh.is_file():
            return ["pip-audit no generó un reporte; instala pipeline/requirements-tools.txt. " + result.stderr[-300:]]
        try:
            report = json.loads(fresh.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            return [f"El reporte de pip-audit no es JSON válido: {error}"]
        if result.returncode not in (0, 1):
            return ["pip-audit no pudo completar la consulta: " + result.stderr[-300:]]
        shutil.copyfile(fresh, output)
    findings = []
    for dependency in report.get("dependencies", []):
        seen = set()
        for vulnerability in dependency.get("vulns", []):
            if vulnerability["id"] in seen:
                continue
            seen.add(vulnerability["id"])
            fixes = ", ".join(vulnerability.get("fix_versions", [])) or "sin versión corregida publicada"
            findings.append(f"{dependency['name']} {dependency['version']}: {vulnerability['id']} (corregir en {fixes})")
    print(f"  pip-audit: {len(findings)} avisos únicos; reporte: reportes/pip_audit.json")
    return findings


def generate_sbom() -> list[str]:
    output = ROOT / "reportes" / "sbom_cyclonedx.json"
    with tempfile.TemporaryDirectory(prefix="dangoko-sbom-") as temp_dir:
        fresh = Path(temp_dir) / "sbom.json"
        result = subprocess.run(
            [sys.executable, "-m", "cyclonedx_py", "requirements", "app/requirements.txt", "--of", "JSON", "--validate", "-o", str(fresh)],
            cwd=ROOT, capture_output=True, text=True,
        )
        if result.returncode:
            return ["CycloneDX no pudo generar el SBOM: " + result.stderr[-500:]]
        try:
            report = json.loads(fresh.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            return [f"El SBOM no es JSON válido: {error}"]
        if report.get("bomFormat") != "CycloneDX" or not report.get("components"):
            return ["El SBOM no contiene componentes CycloneDX"]
        shutil.copyfile(fresh, output)
    print(f"  CycloneDX: {len(report['components'])} componentes; reporte: reportes/sbom_cyclonedx.json")
    return []


def main() -> int:
    print("PIPELINE DANGOKO ENTREGA FINAL")
    print("Umbral: cero avisos HIGH de Bandit, cero vulnerabilidades de dependencias y todas las pruebas correctas")
    checks: list[bool] = []
    checks.append(stage("Pruebas de sintaxis y regresión", tests()))
    checks.append(stage("SAST Bandit", bandit_scan()))
    checks.append(stage("SCA pip-audit", dependency_scan()))
    checks.append(stage("Higiene de secretos", secret_scan(ROOT)))
    checks.append(stage("Infraestructura como código", iac_scan()))
    checks.append(stage("Docker endurecido", docker_scan()))
    checks.append(stage("SBOM CycloneDX", generate_sbom()))
    if all(checks):
        print("\nDECISIÓN FINAL: PERMITIDO")
        return 0
    print("\nDECISIÓN FINAL: BLOQUEADO")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
