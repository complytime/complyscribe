# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Red Hat, Inc.

"""Unit test for sync-cac-content command"""
import os.path
import pathlib
from typing import Tuple

from click.testing import CliRunner
from git import Repo
from ruamel.yaml import YAML

from tests.testutils import TEST_DATA_DIR, setup_for_cac_content_dir, setup_for_compdef
from trestlebot.cli.commands.sync_oscal_content import (
    sync_oscal_cd_to_cac_content_cmd,
    sync_oscal_content_cmd,
    sync_oscal_profile_to_cac_content_cmd,
)
from trestlebot.const import INVALID_ARGS_EXIT_CODE, SUCCESS_EXIT_CODE
from trestlebot.utils import get_comments_from_yaml_data


test_product = "rhel8"
# Note: data in test_content_dir is copied from content repo, PR:
# https://github.com/ComplianceAsCode/content/pull/12819
test_content_dir = TEST_DATA_DIR / "content_dir"


def test_invalid_sync_oscal_cmd() -> None:
    """Tests that sync-oscal-content command fails if given invalid subcommand."""
    runner = CliRunner()
    result = runner.invoke(sync_oscal_content_cmd, ["invalid"])

    assert "Error: No such command 'invalid'" in result.output
    assert result.exit_code == INVALID_ARGS_EXIT_CODE


def test_sync_oscal_cd_to_cac_control(
    tmp_repo: Tuple[str, Repo], tmp_init_dir: str
) -> None:
    """Tests sync OSCAL component definition information to cac content."""
    repo_dir, _ = tmp_repo
    trestle_repo_path = pathlib.Path(repo_dir)
    setup_for_compdef(trestle_repo_path, test_product, test_product)
    tmp_content_dir = tmp_init_dir
    setup_for_cac_content_dir(tmp_content_dir, test_content_dir)

    runner = CliRunner()
    result = runner.invoke(
        sync_oscal_cd_to_cac_content_cmd,
        [
            "--product",
            test_product,
            "--cac-content-root",
            tmp_content_dir,
            "--repo-path",
            str(trestle_repo_path.resolve()),
            "--committer-email",
            "test@email.com",
            "--committer-name",
            "test name",
            "--branch",
            "test",
            "--dry-run",
        ],
    )

    # Check the CLI sync-cac-content is successful
    assert result.exit_code == SUCCESS_EXIT_CODE, result.output

    yaml = YAML()

    # check profile
    profile_path = pathlib.Path(
        os.path.join(tmp_content_dir, "products/rhel8/profiles/example.profile")
    )

    profile_data = yaml.load(profile_path)
    selections_field = profile_data["selections"]
    assert "abcd-levels:all:medium" in selections_field
    assert "file_groupownership_sshd_private_key" not in selections_field
    assert "sshd_set_keepalive" in selections_field
    assert "var_password_pam_minlen=15" in selections_field
    assert "var_sshd_set_keepalive=1" not in selections_field
    assert "no-exist-param=fips" not in selections_field

    # check control file
    control_file_path = pathlib.Path(
        os.path.join(tmp_content_dir, "controls", "abcd-levels.yml")
    )
    control_file_data = yaml.load(control_file_path)
    for control in control_file_data["controls"]:
        if control["id"] == "AC-1":
            # get comment, check if missing rule comment exists
            exist_comments = get_comments_from_yaml_data(control)
            assert len(exist_comments) == 1
            comment = "TODO: Need to implement rule not_exist_rule_id"
            assert len([True for c in exist_comments if comment in c]) == 1
            rules = control.get("rules", [])
            assert "file_groupownership_sshd_private_key" not in rules
            assert "var_system_crypto_policy=not-exist-option" in rules
            assert "var_sshd_set_keepalive=1" not in rules
            assert "not_exist_rule_id" not in rules
            assert "configure_crypto_policy" in rules
            assert control["status"] == "not applicable"
        elif control["id"] == "AC-2":
            rules = control.get("rules", [])
            assert rules == []
            assert control["status"] == "manual"
            exist_comments = get_comments_from_yaml_data(control)
            comment = (
                "The status should be updated to one of "
                "['inherently met', 'documentation', 'automated', 'supported']"
            )
            assert len([True for c in exist_comments if comment in c]) == 1

    # check var file
    var_file_path = pathlib.Path(
        os.path.join(
            tmp_content_dir, "linux_os/guide/test/var_system_crypto_policy.var"
        )
    )
    var_file_data = yaml.load(var_file_path)
    options = var_file_data["options"]
    assert "not-exist-option" in options
    assert options["not-exist-option"] == "not-exist-option"


def test_invalid_sync_oscal_profile_cmd(tmp_repo: Tuple[str, Repo]) -> None:
    """Tests sync OSCAL profile information to cac content."""
    repo_dir, _ = tmp_repo
    trestle_repo_path = pathlib.Path(repo_dir)

    runner = CliRunner()
    result = runner.invoke(
        sync_oscal_profile_to_cac_content_cmd,
        [
            "--cac-policy-id",
            "replace_me",
            "--cac-content-root",
            test_content_dir,
            "--repo-path",
            str(trestle_repo_path.resolve()),
            "--committer-email",
            "test@email.com",
            "--committer-name",
            "test name",
            "--branch",
            "test",
            "--dry-run",
        ],
    )

    assert result.exit_code == SUCCESS_EXIT_CODE, result.output
