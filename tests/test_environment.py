from pathlib import Path
from importlib.metadata import version, PackageNotFoundError


def test_requirements_file_exists():
    assert Path("requirements.txt").exists()


def test_required_packages_installed():
    requirements = Path("requirements.txt")

    try:
        content = requirements.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = requirements.read_text(encoding="utf-16")

    missing = []

    for line in content.splitlines():
        line = line.split("#")[0].strip()   # Remove inline comments

        if not line:
            continue

        package = (
            line.split("==")[0]
                .split(">=")[0]
                .split("<=")[0]
                .split("[")[0]
                .strip()
        )

        try:
            version(package)
        except PackageNotFoundError:
            missing.append(package)

    assert not missing, f"Missing packages: {missing}"