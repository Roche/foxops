import filecmp
import re
import shutil
import typing
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory, mkstemp

from structlog.stdlib import BoundLogger

from foxops.external.git import GitRepository
from foxops.settings import Settings
from foxops.utils import CalledProcessError, check_call


async def diff_and_patch(
    diff_a_directory: Path,
    diff_b_directory: Path,
    patch_directory: Path,
    logger: BoundLogger,
) -> list[Path]:
    patch_path = await diff(diff_a_directory, diff_b_directory, logger=logger)
    try:
        return await patch(
            patch_path,
            patch_directory,
            diff_a_directory,
            diff_b_directory,
            logger=logger,
        )
    finally:
        patch_path.unlink()


@asynccontextmanager
async def setup_diff_git_repository(
    old_directory: Path, new_directory: Path
) -> typing.AsyncGenerator[Path, None]:
    # FIXME(TF): in case the *git way* provides as the viable long-term solution we could directly
    #            bootstrap that intermediate git repository instead of this copy-paste roundtrip.
    settings = Settings()
    git_tmpdir: str
    with TemporaryDirectory() as git_tmpdir:
        await check_call("git", "init", ".", "--initial-branch", "main", cwd=git_tmpdir)
        await check_call(
            "git",
            "config",
            "user.name",
            settings.git_commit_author_name,
            cwd=git_tmpdir,
        )
        await check_call(
            "git",
            "config",
            "user.email",
            settings.git_commit_author_email,
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


async def diff(old_directory: Path, new_directory: Path, logger: BoundLogger) -> Path:
    async with setup_diff_git_repository(old_directory, new_directory) as git_tmpdir:
        logger.debug(f"create git diff between branch old and new in {git_tmpdir}")

        repo = GitRepository(git_tmpdir, logger)
        diff_output = await repo.diff("old", "new")

        patch_path: str
        _, patch_path = mkstemp(prefix="fengine-update-", suffix=".patch")

        (p := Path(patch_path)).write_text(diff_output)
        return p


async def patch(
    patch_path: Path,
    incarnation_root_dir: Path,
    diff_a_directory: Path,
    diff_b_directory: Path,
    logger: BoundLogger,
) -> list[Path]:
    # NOTE(TF): it's crucial that the paths are fully resolved here,
    #           because we are going to fiddle around how they
    #           are relative to each other.
    resolved_incarnation_root_dir = incarnation_root_dir.resolve()
    proc = await check_call(
        "git", "rev-parse", "--show-toplevel", cwd=str(resolved_incarnation_root_dir)
    )
    incarnation_git_root_dir = Path((await proc.stdout.read()).decode("utf-8").strip()).resolve()  # type: ignore
    incarnation_git_dir = (
        resolved_incarnation_root_dir.relative_to(incarnation_git_root_dir)
        if resolved_incarnation_root_dir != incarnation_git_root_dir
        else ""
    )

    # FIXME(TF): may check git status to check if something has been modified or not ...
    logger.debug(
        f"applying patch {patch_path} to {incarnation_git_dir} inside {incarnation_root_dir}"
    )
    try:
        await check_call(
            "git",
            "apply",
            "--reject",  # This option makes it apply the parts of the patch that are applicable, and leave the rejected hunks in corresponding *.rej files.
            "--verbose",
            "--directory",
            str(incarnation_git_dir),
            str(patch_path),
            cwd=str(incarnation_git_root_dir),
        )
    except CalledProcessError as exc:
        logger.debug(
            "detected conflicts with patch, analyzing rejections ...",
            patch_path=patch_path,
        )
        apply_rejection_output = exc.stderr
        files_with_conflicts = await analyze_patch_rejections(
            apply_rejection_output,
            resolved_incarnation_root_dir,
            diff_a_directory,
            diff_b_directory,
            logger=logger,
        )
        return files_with_conflicts
    else:
        return []


async def analyze_patch_rejections(
    apply_rejection_output: bytes,
    patch_directory: Path,
    diff_a_directory: Path,
    diff_b_directory: Path,
    logger: BoundLogger,
) -> list[Path]:
    reject_file_regex = re.compile(rb"Applying patch (.*?) with (\d+) reject...")

    files_with_rejections = []
    for line in apply_rejection_output.splitlines():
        if match := reject_file_regex.match(line):
            files_with_rejections.append(Path(match.group(1).decode()))

    logger.debug(
        f"detected {len(files_with_rejections)} files with rejections",
        files_with_rejections=files_with_rejections,
    )
    files_with_conflicts: list[Path] = []
    for file_with_rejection in files_with_rejections:
        conflict_fixed = await attempt_fixing_rejection(
            file_with_rejection,
            patch_directory,
            diff_a_directory,
            diff_b_directory,
            logger=logger,
        )
        if not conflict_fixed:
            logger.debug(f"file {file_with_rejection} still has conflicts")
            files_with_conflicts.append(file_with_rejection)
    return files_with_conflicts


async def attempt_fixing_rejection(
    file_with_rejection: Path,
    patch_directory: Path,
    diff_a_directory: Path,
    diff_b_directory: Path,
    logger: BoundLogger,
) -> bool:
    # diff_a_file = diff_a_directory / file_with_rejection
    diff_b_file = diff_b_directory / file_with_rejection
    patch_file = patch_directory / file_with_rejection

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
