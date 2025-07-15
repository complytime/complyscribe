# SPDX-License-Identifier: Apache-2.0
# Copyright Red Hat, Inc.

import glob
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Generator, TypeVar

import pytest


root_repo_dir = Path(__file__).resolve().parent.parent.parent
scripts_dir = root_repo_dir / "scripts"
complyctl_cache_dir = Path("/tmp/complyscribe-complyctl-cache")
complyctl_cache_dir.mkdir(parents=True, exist_ok=True)
int_test_data_dir = Path(__file__).parent.parent / "integration_data/"
_TEST_PREFIX = "complyscribe_tests"

T = TypeVar("T")
YieldFixture = Generator[T, None, None]

# Ask complyctl to use home directory instead of hardcoded system paths
os.putenv("COMPLYCTL_DEV_MODE", "1")


def is_complyctl_installed(install_dir: Path) -> bool:
    install_dir / ".local/share/complytime"
    complyctl_bin = install_dir / "bin" / "complyctl"
    openscap_plugin_bin = (
        install_dir / ".local/share/complytime/plugins/openscap-plugin"
    ).resolve()
    openscap_plugin_conf = (
        install_dir / ".local/share/complytime/plugins/c2p-openscap-manifest.json"
    ).resolve()
    return (
        complyctl_bin.exists()
        and openscap_plugin_bin.exists()
        and openscap_plugin_conf.exists()
    )


def is_complyctl_cached(download_dir: Path) -> bool:
    return bool(
        glob.glob(
            str((download_dir / "releases/*/complyctl_linux_x86_64.tar.gz").resolve())
        )
    )


def sha256sum(filepath: Path) -> str:
    sha256 = hashlib.sha256()
    chunk_size = 65536
    with open(filepath, "rb") as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            sha256.update(chunk)
        return sha256.hexdigest()


@pytest.fixture(autouse=True)
def complyctl_home() -> YieldFixture[Path]:
    # Setup
    complyctl_cache_dir.mkdir(parents=True, exist_ok=True)
    complyctl_home = Path(tempfile.mkdtemp(prefix=_TEST_PREFIX))
    orig_home = os.getenv("HOME")
    orig_path = os.getenv("PATH")
    orig_xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    orig_xdg_data_home = os.getenv("XDG_DATA_HOME")

    complyctl_home.mkdir(parents=True, exist_ok=True)
    if not is_complyctl_installed(complyctl_home):
        if not is_complyctl_cached(complyctl_cache_dir):
            result = subprocess.run(
                [
                    scripts_dir / "get-github-release.py",
                    "https://github.com/complytime/complyctl",
                ],
                cwd=complyctl_cache_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise ValueError(
                    "Unable to install Complyctl for integration test!"
                    f"\n{result.stdout}"
                    f"\n{result.stderr}"
                )
        result = subprocess.run(
            [
                "find",
                f"{complyctl_cache_dir}/releases",
                "-name",
                "complyctl_linux_x86_64.tar.gz",
                "-exec",
                "tar",
                "-xvf",
                "{}",
                ";",
                "-quit",
            ],
            cwd=complyctl_home,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise ValueError(
                f"Unable to extract Complyctl for integration test!\n{result.stdout}\n{result.stderr}"
            )

        # Install complyctl
        install_complyctl(complyctl_home)

        # Create dummy base files
        shutil.copy(
            int_test_data_dir / "sample-catalog.json",
            complyctl_home / ".local/share/complytime/controls/sample-catalog.json",
        )
        shutil.copy(
            int_test_data_dir / "sample-profile.json",
            complyctl_home / ".local/share/complytime/controls/sample-profile.json",
        )
        shutil.copy(
            int_test_data_dir / "sample-component-definition.json",
            complyctl_home
            / ".local/share/complytime/bundles/sample-component-definition.json",
        )

    os.environ["HOME"] = str(complyctl_home)
    os.environ["XDG_CONFIG_HOME"] = str(complyctl_home / ".config")
    os.environ["XDG_DATA_HOME"] = str(complyctl_home / ".local/share")
    os.environ["PATH"] = str(complyctl_home / "bin") + ":" + os.environ["PATH"]

    yield complyctl_home  # run the test

    # Teardown
    if orig_home is None:
        os.unsetenv("HOME")
    else:
        os.environ["HOME"] = orig_home
    if orig_path is None:
        os.unsetenv("PATH")
    else:
        os.environ["PATH"] = orig_path
    if orig_xdg_config_home is None:
        os.unsetenv("XDG_CONFIG_HOME")
    else:
        os.environ["XDG_CONFIG_HOME"] = orig_xdg_config_home
    if orig_xdg_data_home is None:
        os.unsetenv("XDG_DATA_HOME")
    else:
        os.environ["XDG_DATA_HOME"] = orig_xdg_data_home
    shutil.rmtree(complyctl_home)


def install_complyctl(complyctl_home: Path) -> None:
    Path(complyctl_home / "bin/").mkdir(parents=True, exist_ok=True)
    Path(complyctl_home / ".local/share/complytime/plugins/").mkdir(
        parents=True, exist_ok=True
    )
    Path(complyctl_home / ".local/share/complytime/bundles/").mkdir(
        parents=True, exist_ok=True
    )
    Path(complyctl_home / ".local/share/complytime/controls/").mkdir(
        parents=True, exist_ok=True
    )
    shutil.move(complyctl_home / "complyctl", complyctl_home / "bin/complyctl")
    shutil.move(
        complyctl_home / "openscap-plugin",
        complyctl_home / ".local/share/complytime/plugins/openscap-plugin",
    )
    openscap_plugin_sha256 = sha256sum(
        complyctl_home / ".local/share/complytime/plugins/openscap-plugin"
    )
    with open(
        int_test_data_dir / "c2p-openscap-manifest.json"
    ) as c2p_openscap_manifest_file:
        c2p_openscap_manifest = json.load(c2p_openscap_manifest_file)
        c2p_openscap_manifest["sha256"] = openscap_plugin_sha256
        with open(
            complyctl_home
            / ".local/share/complytime/plugins/c2p-openscap-manifest.json",
            "w",
        ) as templated_file:
            json.dump(c2p_openscap_manifest, templated_file)
