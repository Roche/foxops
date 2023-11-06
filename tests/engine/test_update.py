import shutil
from pathlib import Path

import pytest

from foxops import utils
from foxops.engine import diff_and_patch, initialize_incarnation, update_incarnation
from foxops.engine.models.template_config import (
    StringVariableDefinition,
    TemplateConfig,
)


async def init_repository(repository_dir: Path) -> None:
    await utils.check_call("git", "init", cwd=repository_dir)
    await utils.check_call("git", "config", "user.name", "test", cwd=repository_dir)
    await utils.check_call("git", "config", "user.email", "test@test.com", cwd=repository_dir)
    await utils.check_call("git", "add", ".", cwd=repository_dir)
    await utils.check_call("git", "commit", "-m", "initial commit", cwd=repository_dir)
    proc = await utils.check_call("git", "rev-parse", "HEAD", cwd=repository_dir)
    return (await proc.stdout.read()).decode().strip()  # type: ignore


@pytest.mark.parametrize(
    "diff_patch_func",
    [diff_and_patch],
)
async def test_diff_and_patch_update_single_file_without_conflict(diff_patch_func, tmp_path):
    # GIVEN
    old_directory = tmp_path / "old"
    old_directory.mkdir()
    (old_directory / "file.txt").write_text("old content")
    new_directory = tmp_path / "new"
    to_patch_directory = tmp_path / "to_patch"
    shutil.copytree(old_directory, to_patch_directory)
    await init_repository(to_patch_directory)
    shutil.copytree(old_directory, new_directory)
    (new_directory / "file.txt").write_text("new content")

    # WHEN
    await diff_patch_func(
        diff_a_directory=old_directory,
        diff_b_directory=new_directory,
        patch_directory=to_patch_directory,
    )

    # THEN
    assert (to_patch_directory / "file.txt").read_text() == "new content"


@pytest.mark.parametrize("diff_patch_func", [diff_and_patch])
async def test_diff_and_patch_adding_new_file_without_conflict(diff_patch_func, tmp_path):
    # GIVEN
    old_directory = tmp_path / "old"
    old_directory.mkdir()
    (old_directory / "file.txt").write_text("any content")
    new_directory = tmp_path / "new"
    to_patch_directory = tmp_path / "to_patch"
    shutil.copytree(old_directory, to_patch_directory)
    await init_repository(to_patch_directory)
    shutil.copytree(old_directory, new_directory)
    (new_directory / "new-file.txt").write_text("new content")

    # WHEN
    await diff_patch_func(
        diff_a_directory=old_directory,
        diff_b_directory=new_directory,
        patch_directory=to_patch_directory,
    )

    # THEN
    assert (to_patch_directory / "new-file.txt").read_text() == "new content"


@pytest.mark.parametrize("diff_patch_func", [diff_and_patch])
async def test_diff_and_patch_removing_file_without_conflict(diff_patch_func, tmp_path):
    # GIVEN
    old_directory = tmp_path / "old"
    old_directory.mkdir()
    (old_directory / "file.txt").write_text("any content")
    (old_directory / "deprecated-file.txt").write_text("deprecated content")
    new_directory = tmp_path / "new"
    to_patch_directory = tmp_path / "to_patch"
    shutil.copytree(old_directory, to_patch_directory)
    await init_repository(to_patch_directory)
    shutil.copytree(old_directory, new_directory)
    (new_directory / "deprecated-file.txt").unlink()

    # WHEN
    await diff_patch_func(
        diff_a_directory=old_directory,
        diff_b_directory=new_directory,
        patch_directory=to_patch_directory,
    )

    # THEN
    assert not (to_patch_directory / "deprecated-file.txt").exists()


@pytest.mark.parametrize("diff_patch_func", [diff_and_patch])
async def test_diff_and_patch_no_change_when_updating_to_template_version_with_identical_change(
    diff_patch_func,
    tmp_path,
):
    """
    Verify that no change is being made to the incarnation repository when updating to a template version
    which contains the same changes as the incarnation.
    """
    # GIVEN
    template_directory = tmp_path / "template"
    template_directory.mkdir()

    (template_directory / "template").mkdir()
    (template_directory / "template" / "myfile.txt").write_text(
        """r1 {...}

r2 {...}
"""
    )
    await init_repository(tmp_path)
    incarnation_directory = tmp_path / "incarnation"
    incarnation_directory.mkdir()

    incarnation_state = await initialize_incarnation(
        template_root_dir=template_directory,
        template_repository="any-repository-url",
        template_repository_version="any-version",
        template_data={},
        incarnation_root_dir=incarnation_directory,
    )

    # WHEN
    # same change in template and incarnation
    updated_template_directory = tmp_path / "updated-template"
    shutil.copytree(template_directory, updated_template_directory)
    (updated_template_directory / "template" / "myfile.txt").write_text(
        """r1 {...}

rnew {...}

r2 {...}
"""
    )
    (incarnation_directory / "myfile.txt").write_text(
        """r1 {...}

rnew {...}

r2 {...}
"""
    )
    await init_repository(incarnation_directory)

    await update_incarnation(
        original_template_root_dir=template_directory,
        updated_template_root_dir=updated_template_directory,
        updated_template_repository_version=incarnation_state.template_repository_version,
        updated_template_data=incarnation_state.template_data,
        incarnation_root_dir=incarnation_directory,
        diff_patch_func=diff_patch_func,
    )

    # THEN
    assert (incarnation_directory / "myfile.txt").read_text() == (
        """r1 {...}

rnew {...}

r2 {...}
"""
    )


@pytest.mark.parametrize("diff_patch_func", [diff_and_patch])
async def test_diff_and_patch_no_change_when_updating_to_template_version_with_identical_change_in_subdirectory(
    diff_patch_func,
    tmp_path,
):
    """
    Verify that no change is being made to the incarnation repository when updating to a template version
    which contains the same changes as the incarnation.

    This test verifies things are working correctly when the incarnation was initialized in a subdirectory
    of a git repository.
    """
    # GIVEN
    template_directory = tmp_path / "template"
    template_directory.mkdir()

    (template_directory / "template").mkdir()
    (template_directory / "template" / "myfile.txt").write_text(
        """r1 {...}

r2 {...}
"""
    )
    await init_repository(tmp_path)

    incarnation_repository_directory = tmp_path / "incarnation"
    incarnation_repository_directory.mkdir()

    incarnation_directory = incarnation_repository_directory / "subdir"
    incarnation_directory.mkdir()

    incarnation_state = await initialize_incarnation(
        template_root_dir=template_directory,
        template_repository="any-repository-url",
        template_repository_version="any-version",
        template_data={},
        incarnation_root_dir=incarnation_directory,
    )
    await init_repository(incarnation_repository_directory)

    # WHEN
    # same change in template and incarnation
    updated_template_directory = tmp_path / "updated-template"
    shutil.copytree(template_directory, updated_template_directory)
    (updated_template_directory / "template" / "myfile.txt").write_text(
        """r1 {...}

rnew {...}

r2 {...}
"""
    )
    (incarnation_directory / "myfile.txt").write_text(
        """r1 {...}

rnew {...}

r2 {...}
"""
    )

    await update_incarnation(
        original_template_root_dir=template_directory,
        updated_template_root_dir=updated_template_directory,
        updated_template_repository_version=incarnation_state.template_repository_version,
        updated_template_data=incarnation_state.template_data,
        incarnation_root_dir=incarnation_directory,
        diff_patch_func=diff_patch_func,
    )

    # THEN
    assert (incarnation_directory / "myfile.txt").read_text() == (
        """r1 {...}

rnew {...}

r2 {...}
"""
    )


@pytest.mark.parametrize("diff_patch_func", [diff_and_patch])
async def test_diff_and_patch_conflict_for_nearby_changes_in_template_and_incarnation(
    diff_patch_func,
    tmp_path,
):
    """
    Verify that a conflict is detected when updating to a template version
    which contains a change nearby a change in the incarnation.
    """
    # GIVEN
    template_directory = tmp_path / "template"
    template_directory.mkdir()

    (template_directory / "template").mkdir()
    (template_directory / "template" / "myfile.txt").write_text(
        """a
b
c
"""
    )
    await init_repository(tmp_path)
    incarnation_directory = tmp_path / "incarnation"
    incarnation_directory.mkdir()

    incarnation_state = await initialize_incarnation(
        template_root_dir=template_directory,
        template_repository="any-repository-url",
        template_repository_version="any-version",
        template_data={},
        incarnation_root_dir=incarnation_directory,
    )

    # WHEN
    # nearby change in template and incarnation
    updated_template_directory = tmp_path / "updated-template"
    shutil.copytree(template_directory, updated_template_directory)
    (updated_template_directory / "template" / "myfile.txt").write_text(
        """a
b
a
"""
    )
    (incarnation_directory / "myfile.txt").write_text(
        """c
b
c
"""
    )
    await init_repository(incarnation_directory)

    # WHEN
    update_performed, _, patch_result = await update_incarnation(
        original_template_root_dir=template_directory,
        updated_template_root_dir=updated_template_directory,
        updated_template_repository_version=incarnation_state.template_repository_version,
        updated_template_data=incarnation_state.template_data,
        incarnation_root_dir=incarnation_directory,
        diff_patch_func=diff_patch_func,
    )

    # THEN
    assert update_performed is True
    assert Path("myfile.txt") in patch_result.conflicts


@pytest.mark.parametrize("diff_patch_func", [diff_and_patch])
async def test_diff_and_patch_success_when_changes_in_different_places_in_template_and_incarnation(
    diff_patch_func,
    tmp_path,
):
    """
    Verify that a incarnation can successfully be updated to a new template version
    if both contain locality unrelated changes.
    """
    # GIVEN
    template_directory = tmp_path / "template"
    template_directory.mkdir()

    (template_directory / "template").mkdir()
    (template_directory / "template" / "myfile.txt").write_text(
        """a
b
c

###
### Add custom changes to this file below
###
"""
    )
    await init_repository(tmp_path)
    incarnation_directory = tmp_path / "incarnation"
    incarnation_directory.mkdir()

    incarnation_state = await initialize_incarnation(
        template_root_dir=template_directory,
        template_repository="any-repository-url",
        template_repository_version="any-version",
        template_data={},
        incarnation_root_dir=incarnation_directory,
    )

    # WHEN
    # same change in template and incarnation
    updated_template_directory = tmp_path / "updated-template"
    shutil.copytree(template_directory, updated_template_directory)
    (updated_template_directory / "template" / "myfile.txt").write_text(
        """a
b1
b2
c

###
### Add custom changes to this file below
###
"""
    )
    (incarnation_directory / "myfile.txt").write_text(
        """a
b
c

###
### Add custom changes to this file below
###
mychange
"""
    )
    await init_repository(incarnation_directory)

    await update_incarnation(
        original_template_root_dir=template_directory,
        updated_template_root_dir=updated_template_directory,
        updated_template_repository_version=incarnation_state.template_repository_version,
        updated_template_data=incarnation_state.template_data,
        incarnation_root_dir=incarnation_directory,
        diff_patch_func=diff_patch_func,
    )

    # THEN
    assert (
        (incarnation_directory / "myfile.txt").read_text()
        == """a
b1
b2
c

###
### Add custom changes to this file below
###
mychange
"""
    )


@pytest.mark.parametrize("diff_patch_func", [diff_and_patch])
async def test_diff_and_patch_success_when_deleting_file_in_template(
    diff_patch_func,
    tmp_path,
):
    """
    Verify that a file is successfully deleted from the incarnation if it has been deleted in the template.
    """
    # GIVEN
    template_directory = tmp_path / "template"
    template_directory.mkdir()

    (template_directory / "template").mkdir()
    (template_directory / "template" / "myfile1.txt").write_text("some content")
    (template_directory / "template" / "myfile2.txt").write_text("more content")
    await init_repository(tmp_path)

    incarnation_directory = tmp_path / "incarnation"
    incarnation_directory.mkdir()
    incarnation_state = await initialize_incarnation(
        template_root_dir=template_directory,
        template_repository="any-repository-url",
        template_repository_version="any-version",
        template_data={},
        incarnation_root_dir=incarnation_directory,
    )

    # WHEN
    # same change in template and incarnation
    updated_template_directory = tmp_path / "updated-template"
    shutil.copytree(template_directory, updated_template_directory)
    (updated_template_directory / "template" / "myfile2.txt").unlink()

    await utils.check_call("git", "init", ".", cwd=str(incarnation_directory))
    await utils.check_call("git", "config", "user.name", "test", cwd=str(incarnation_directory))
    await utils.check_call("git", "config", "user.email", "test@test.com", cwd=str(incarnation_directory))
    await utils.check_call("git", "add", ".", cwd=str(incarnation_directory))
    await utils.check_call("git", "commit", "-am", "Initial commit", cwd=str(incarnation_directory))

    await update_incarnation(
        original_template_root_dir=template_directory,
        updated_template_root_dir=updated_template_directory,
        updated_template_repository_version=incarnation_state.template_repository_version,
        updated_template_data=incarnation_state.template_data,
        incarnation_root_dir=incarnation_directory,
        diff_patch_func=diff_patch_func,
    )

    # THEN
    assert (incarnation_directory / "myfile1.txt").exists()
    assert not (incarnation_directory / "myfile2.txt").exists()


@pytest.mark.parametrize("diff_patch_func", [diff_and_patch])
async def test_diff_and_patch_success_when_changed_file_is_deleted_in_incarnation(
    diff_patch_func,
    tmp_path,
):
    # GIVEN
    template_directory = tmp_path / "template"
    template_directory.mkdir()

    (template_directory / "template").mkdir()
    (template_directory / "template" / "myfile1.txt").write_text("some content")
    (template_directory / "template" / "myfile2.txt").write_text("more content")
    await init_repository(tmp_path)

    incarnation_directory = tmp_path / "incarnation"
    incarnation_directory.mkdir()
    incarnation_state = await initialize_incarnation(
        template_root_dir=template_directory,
        template_repository="any-repository-url",
        template_repository_version="any-version",
        template_data={},
        incarnation_root_dir=incarnation_directory,
    )

    # WHEN
    # file is changed in template
    # ... and at the same time deleted in the incarnation
    updated_template_directory = tmp_path / "updated-template"
    shutil.copytree(template_directory, updated_template_directory)
    (updated_template_directory / "template" / "myfile2.txt").write_text("new content")

    await utils.check_call("git", "init", ".", cwd=str(incarnation_directory))
    await utils.check_call("git", "config", "user.name", "test", cwd=str(incarnation_directory))
    await utils.check_call("git", "config", "user.email", "test@test.com", cwd=str(incarnation_directory))
    await utils.check_call("git", "add", ".", cwd=str(incarnation_directory))
    await utils.check_call("git", "commit", "-am", "Initial commit", cwd=str(incarnation_directory))

    (incarnation_directory / "myfile2.txt").unlink()
    _, _, patch_result = await update_incarnation(
        original_template_root_dir=template_directory,
        updated_template_root_dir=updated_template_directory,
        updated_template_repository_version=incarnation_state.template_repository_version,
        updated_template_data=incarnation_state.template_data,
        incarnation_root_dir=incarnation_directory,
        diff_patch_func=diff_patch_func,
    )

    # THEN
    assert Path("myfile2.txt") in patch_result.deleted

    assert (incarnation_directory / "myfile1.txt").exists()
    assert not (incarnation_directory / "myfile2.txt").exists()
    # `git apply --reject` does not keep .rej files when the target file was deleted (unfortunately)


async def test_update_incarnation_with_change_of_default_values_in_template(tmp_path):
    """
    When updating an incarnation to a newer template version, a change of the default value of template variables
    should be reflected in the updated incarnation (if the user did not explicitly specify a value) for those vars.
    """

    # GIVEN
    # ... a template with variables that have defaults
    template_directory = tmp_path / "template"
    template_directory.mkdir()

    TemplateConfig(
        variables={
            "variable_specified": StringVariableDefinition(description="dummy", default="abc"),
            "variable_not_specified": StringVariableDefinition(description="dummy", default="1"),
        }
    ).save(template_directory / "fengine.yaml")
    (template_directory / "template").mkdir()
    (template_directory / "template" / "var1.txt").write_text("value: {{ variable_specified }}")
    (template_directory / "template" / "var2.txt").write_text("value: {{ variable_not_specified }}")
    await init_repository(template_directory)

    # ... an updated version of the template where the variable defaults changed
    template_updated_directory = tmp_path / "template-updated"
    shutil.copytree(template_directory, template_updated_directory)

    template_updated_config = TemplateConfig.from_path(template_updated_directory / "fengine.yaml")
    template_updated_config.variables["variable_specified"].default = "xyz"
    template_updated_config.variables["variable_not_specified"].default = "2"
    template_updated_config.save(template_updated_directory / "fengine.yaml")

    # ... and an incarnation of the original template version, where only one of the variables is specified by the user
    incarnation_directory = tmp_path / "incarnation"
    incarnation_directory.mkdir()
    incarnation_state = await initialize_incarnation(
        template_root_dir=template_directory,
        template_repository="any-repository-url",
        template_repository_version="any-version",
        template_data={
            "variable_specified": "user-specified-value",
        },
        incarnation_root_dir=incarnation_directory,
    )
    await init_repository(incarnation_directory)

    assert (incarnation_directory / "var1.txt").read_text() == "value: user-specified-value"
    assert (incarnation_directory / "var2.txt").read_text() == "value: 1"

    # WHEN
    # ... the incarnation is updated to the new template version
    await update_incarnation(
        original_template_root_dir=template_directory,
        updated_template_root_dir=template_updated_directory,
        updated_template_repository_version=incarnation_state.template_repository_version,
        updated_template_data=incarnation_state.template_data,
        incarnation_root_dir=incarnation_directory,
        diff_patch_func=diff_and_patch,
    )

    # THEN
    assert (incarnation_directory / "var1.txt").read_text() == "value: user-specified-value"
    assert (incarnation_directory / "var2.txt").read_text() == "value: 2"
