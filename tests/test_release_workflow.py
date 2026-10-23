"""Check release identity guards and version inference from an actual Git tag."""

import importlib.util
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "arr_verify_release", _ROOT / ".github/workflows/verify_release.py"
)
assert _SPEC is not None and _SPEC.loader is not None
_RELEASE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_RELEASE)


class ReleaseValidationTests(unittest.TestCase):
    def artifacts(self, directory, *, name="yamcps-arr", version="1.2.3", package="yamcps_arr"):
        metadata = f"Metadata-Version: 2.4\nName: {name}\nVersion: {version}\n"
        with zipfile.ZipFile(directory / "package.whl", "w") as archive:
            archive.writestr("yamcps_arr-1.2.3.dist-info/METADATA", metadata)
            archive.writestr(f"{package}/__init__.py", "")
        info = directory / "PKG-INFO"
        info.write_text(metadata)
        with tarfile.open(directory / "package.tar.gz", "w:gz") as archive:
            archive.add(info, arcname="package/PKG-INFO")
        info.unlink()

    def test_matching_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.artifacts(directory)
            _RELEASE.verify(directory, "v1.2.3")

    def test_wrong_identity_version_and_unexpected_package(self):
        for kwargs in (
            {"name": "yamcps"},
            {"version": "1.2.4.dev1"},
            {"package": "yamcps_sonarr"},
        ):
            with self.subTest(kwargs=kwargs), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                self.artifacts(directory, **kwargs)
                with self.assertRaises(ValueError):
                    _RELEASE.verify(directory, "v1.2.3")

    def test_invalid_tag_missing_and_extra_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            self.artifacts(directory)
            for tag in ("1.2.3", "v", "v1.2.4"):
                with self.subTest(tag=tag), self.assertRaises(ValueError):
                    _RELEASE.verify(directory, tag)
            (directory / "extra.whl").touch()
            with self.assertRaises(ValueError):
                _RELEASE.verify(directory, "v1.2.3")
            (directory / "extra.whl").unlink()
            (directory / "package.whl").unlink()
            with self.assertRaises(ValueError):
                _RELEASE.verify(directory, "v1.2.3")

    def test_build_version_comes_from_tag(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for name in ("src", ".github"):
                shutil.copytree(_ROOT / name, directory / name)
            for name in ("pyproject.toml", "README.md", "LICENSE"):
                shutil.copy2(_ROOT / name, directory / name)

            def run(*args):
                return subprocess.run(
                    args, cwd=directory, check=True, capture_output=True, text=True
                )

            run("git", "init", "--initial-branch=main")
            run("git", "add", ".")
            run(
                "git",
                "-c",
                "user.name=Release Test",
                "-c",
                "user.email=test@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-m",
                "Test version from tag",
            )
            run("git", "tag", "v1.2.3")
            run(sys.executable, "-m", "build", "--no-isolation", "--outdir", "dist")
            _RELEASE.verify(directory / "dist", "v1.2.3")
            self.assertEqual(
                {path.name for path in (directory / "dist").iterdir()},
                {"yamcps_arr-1.2.3-py3-none-any.whl", "yamcps_arr-1.2.3.tar.gz"},
            )


if __name__ == "__main__":
    unittest.main()
