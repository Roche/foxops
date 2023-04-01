import filecmp
import os
import re
import shutil
import typing
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory, mkstemp

from foxops.external.git import GitRepository
from foxops.logger import get_logger
from foxops.utils import CalledProcessError, check_call

#: Holds the module logger
logger = get_logger(__name__)


@dataclass
class PatchResult:
    # file paths that should have been patched, but could not because of a conflict
    conflicts: list[Path]
    # file paths that should have been patched, but could not because of a missing file
    deleted: list[Path]

    def has_errors(self) -> bool:
        return len(self.conflicts) >= 1 or len(self.deleted) >= 1


async def diff_and_patch(
    diff_a_directory: Path,
    diff_b_directory: Path,
    patch_directory: Path,
) -> PatchResult | None:
    if (patch_path := await diff(diff_a_directory, diff_b_directory)) is not None:
        try:
            return await patch(
                patch_path,
                patch_directory,
                diff_b_directory,
            )
        finally:
            patch_path.unlink()
    return None


@asynccontextmanager
async def setup_diff_git_repository(old_directory: Path, new_directory: Path) -> typing.AsyncGenerator[Path, None]:
    # FIXME(TF): in case the *git way* provides as the viable long-term solution we could directly
    #            bootstrap that intermediate git repository instead of this copy-paste roundtrip.
    git_tmpdir: str
    with TemporaryDirectory() as git_tmpdir:
        await check_call("git", "init", ".", "--initial-branch", "main", cwd=git_tmpdir)
        await check_call(
            "git",
            "config",
            "user.name",
            "fengine",
            cwd=git_tmpdir,
        )
        await check_call(
            "git",
            "config",
            "user.email",
            "noreply@fengine.io",
            cwd=git_tmpdir,
        )
        await check_call(
            "git",
            "commit",
            "--allow-empty",
            "-m",
            "empty initial commit",
            cwd=git_tmpdir,
        )
        await check_call("git", "switch", "--create", "old", "main", cwd=git_tmpdir)
        shutil.copytree(old_directory, git_tmpdir, dirs_exist_ok=True)
        await check_call("git", "add", ".", cwd=git_tmpdir)
        await check_call("git", "commit", "-m", "old template status", cwd=git_tmpdir)
        await check_call("git", "switch", "--create", "new", "main", cwd=git_tmpdir)
        shutil.copytree(new_directory, git_tmpdir, dirs_exist_ok=True)
        await check_call("git", "add", ".", cwd=git_tmpdir)
        await check_call("git", "commit", "-m", "new template status", cwd=git_tmpdir)

        yield Path(git_tmpdir)


async def diff(old_directory: Path, new_directory: Path) -> Path | None:
    async with setup_diff_git_repository(old_directory, new_directory) as git_tmpdir:
        logger.debug(f"create git diff between branch old and new in {git_tmpdir}")

        repo = GitRepository(git_tmpdir)
        diff_output = await repo.diff("old", "new")

        if diff_output == "":
            logger.info("The update didn't change anything, no patch to create")
            return None

        logger.debug("create patch from git diff", diff_output=diff_output)
        fd, patch_path = mkstemp(prefix="fengine-update-", suffix=".patch")
        os.close(fd)

        (p := Path(patch_path)).write_text(diff_output)
        return p


async def patch(
    patch_path: Path,
    incarnation_root_dir: Path,
    rendered_updated_template_directory: Path,
) -> PatchResult:
    # NOTE(TF): it's crucial that the paths are fully resolved here,
    #           because we are going to fiddle around how they
    #           are relative to each other.
    resolved_incarnation_root_dir = incarnation_root_dir.resolve()
    proc = await check_call("git", "rev-parse", "--show-toplevel", cwd=str(resolved_incarnation_root_dir))
    incarnation_repository_dir = Path((await proc.stdout.read()).decode("utf-8").strip()).resolve()  # type: ignore
    incarnation_subdir = (
        resolved_incarnation_root_dir.relative_to(incarnation_repository_dir)
        if resolved_incarnation_root_dir != incarnation_repository_dir
        else None
    )

    # FIXME(TF): may check git status to check if something has been modified or not ...
    logger.debug(f"applying patch {patch_path} to {incarnation_subdir} inside {incarnation_root_dir}")
    try:
        # The `--reject` option makes it apply the parts of the patch that are applicable,
        # and leave the rejected hunks in corresponding *.rej files.
        git_apply_options = [
            "--reject",
            "--verbose",
        ]
        if incarnation_subdir is not None:
            git_apply_options.extend(["--directory", str(incarnation_subdir)])

        await check_call(
            "git",
            "apply",
            *git_apply_options,
            str(patch_path),
            cwd=str(incarnation_repository_dir),
        )
    except CalledProcessError as exc:
        logger.debug(
            "detected conflicts with patch, analyzing rejections ...",
            patch_path=patch_path,
            exc=exc,
        )
        apply_rejection_output = exc.stderr
        return await analyze_patch_rejections(
            apply_rejection_output,
            incarnation_repository_dir,
            incarnation_subdir,
            rendered_updated_template_directory,
        )
    else:
        return PatchResult(conflicts=[], deleted=[])


async def analyze_patch_rejections(
    apply_rejection_output: bytes,
    incarnation_repository_dir: Path,
    incarnation_subdir: Path | None,
    rendered_updated_template_directory: Path,
) -> PatchResult:
    if incarnation_subdir is None:
        incarnation_dir = incarnation_repository_dir
    else:
        incarnation_dir = incarnation_repository_dir / incarnation_subdir

    patch_outcome = parse_git_apply_rejection_output(apply_rejection_output)

    files_with_conflicts: list[Path] = []
    for file_with_rejection in patch_outcome.conflicts:
        conflict_fixed = await attempt_fixing_rejection(
            (incarnation_repository_dir / file_with_rejection).relative_to(incarnation_dir),
            incarnation_dir,
            rendered_updated_template_directory,
        )
        if not conflict_fixed:
            logger.debug(f"file {file_with_rejection} still has conflicts")
            files_with_conflicts.append(file_with_rejection)
    return PatchResult(conflicts=files_with_conflicts, deleted=patch_outcome.deleted)


async def attempt_fixing_rejection(
    file_with_rejection: Path,
    patch_directory: Path,
    diff_b_directory: Path,
) -> bool:
    diff_b_file = diff_b_directory / file_with_rejection
    patch_file = patch_directory / file_with_rejection
    if not diff_b_file.exists() or not patch_file.exists():
        logger.info("could not fix rejection - file doesn't exist anymore", file=file_with_rejection)
        return False

    logger.debug(f"attempting to fix rejection for file {file_with_rejection} ...")

    if filecmp.cmp(diff_b_file, patch_file, shallow=True):
        # the rejected hunk tried to apply a change which was already applied,
        # we can safely remove the rejection file.
        (patch_file.with_suffix(patch_file.suffix + ".rej")).unlink()
        logger.debug(
            f"the rejection was caused because the two files are identical, mark {file_with_rejection} as fixed"
        )
        return True

    return False


def parse_git_apply_rejection_output(output: bytes) -> PatchResult:
    """
    Parse the output of `git apply --reject` to extract the list of files.

    Returns:
        list[Path]: the list of filenames with rejections. The returned paths are relative to the repository root.
        list[Path]: the list of filenames that have changes but have been deleted in the incarnation.
                    The returned paths are relative to the repository root.
    """
    reject_file_regex = re.compile(rb"Applying patch (.*?) with (\d+) reject...")
    deleted_target_regex = re.compile(rb"error: (.*): No such file or directory")

    files_with_rejections = []
    deleted_target_files = []
    for line in output.splitlines():
        if match := reject_file_regex.match(line):
            files_with_rejections.append(Path(match.group(1).decode()))
        if match := deleted_target_regex.match(line):
            deleted_target_files.append(Path(match.group(1).decode()))

    logger.debug(
        f"detected {len(files_with_rejections)} files with rejections and {len(deleted_target_files)} deleted target files",
        files_with_rejections=files_with_rejections,
        deleted_target_files=deleted_target_files,
    )

    return PatchResult(conflicts=files_with_rejections, deleted=deleted_target_files)
