import functools
import os
import typing
from pathlib import Path

from aiopath import AsyncPath
from jinja2 import FileSystemLoader, StrictUndefined
from jinja2.sandbox import SandboxedEnvironment

from foxops.engine.custom_filters import base64encode, ip_add_integer
from foxops.engine.models import TemplateData
from foxops.logger import get_logger

#: Holds the module logger
logger = get_logger(__name__)


def create_template_environment(template_root_dir: Path) -> SandboxedEnvironment:
    """Create a virtual environment to render a template into an incarnation.

    As of now the environment is an untouched jinja2 sandboxed environment
    which only has access to the template root directory.
    """
    paths = [template_root_dir]
    loader = FileSystemLoader(paths)
    # NOTE(TF): add extensions to the loader if necessary.
    env = SandboxedEnvironment(
        loader=loader,
        enable_async=True,
        keep_trailing_newline=True,
        undefined=StrictUndefined,
    )
    env.filters["ip_add_integer"] = ip_add_integer
    env.filters["base64encode"] = base64encode
    return env


async def render_template(
    template_root_dir: Path,
    incarnation_root_dir: Path,
    template_data: TemplateData,
    rendering_filename_exclude_patterns: list[str],
) -> None:
    """Render a template into an incarnation.

    As of now a very simplistic approach is used to find and render the files
    and folders in a template.

    :param rendering_filename_exclude_patterns: A list of glob patterns matching files which contents should not be
    rendered. Can be empty.
    """
    if not template_root_dir.is_absolute():
        raise ValueError(f"template_root_dir must be an absolute path, got {template_root_dir}")

    files_to_render = set(template_root_dir.glob("**/*"))
    for pattern in rendering_filename_exclude_patterns:
        files_to_render -= set(template_root_dir.glob(pattern))

    environment = create_template_environment(template_root_dir)

    logger.debug(
        "start rendering template",
        template_root_dir=template_root_dir,
        incarnation_root_dir=incarnation_root_dir,
        template_data=template_data,
        rendering_filename_exclude_patterns=rendering_filename_exclude_patterns,
    )

    async def _render_template_symlink(template_symlink_path):
        return await render_template_symlink(
            environment,
            template_symlink_path,
            incarnation_root_dir,
            template_data,
        )

    async def _render_template_dir(template_dir_path):
        return await render_template_dir(
            environment,
            template_dir_path,
            incarnation_root_dir,
            template_data,
        )

    async def _render_template_file(template_file_path, render_content: bool):
        return await render_template_file(
            environment,
            template_file_path,
            incarnation_root_dir,
            template_data,
            render_content=render_content,
        )

    for root_dir, dirs, files in os.walk(template_root_dir):
        for d in dirs:
            template_dir_path = Path(root_dir) / d
            if template_dir_path.is_symlink():
                await _render_template_symlink(template_dir_path)
            else:
                await _render_template_dir(template_dir_path)

        for f in files:
            template_file_path = Path(root_dir) / f
            if template_file_path.is_symlink():
                await _render_template_symlink(template_file_path)
            else:
                await _render_template_file(
                    template_file_path,
                    render_content=template_file_path in files_to_render,
                )


async def render_template_file(
    environment: SandboxedEnvironment,
    template_file_path: Path,
    incarnation_root_dir: Path,
    template_data: TemplateData,
    render_content: bool,
) -> Path:
    """Render a template file into an incarnation file.

    The template file content and file name are rendered if rendering_enabled is True. Otherwise, rendering of the file
    content is skipped.
    """
    loader: FileSystemLoader = typing.cast(FileSystemLoader, environment.loader)
    relative_template_path = template_file_path.relative_to(loader.searchpath[0])

    rendered_content: typing.Union[str, bytes]
    if render_content:
        # get and render template file contents
        content_template = environment.get_template(str(relative_template_path))
        rendered_content = await content_template.render_async(**template_data)
    else:
        rendered_content = template_file_path.read_bytes()

    # get and render template file path
    # NOTE (AH): Even when file content rendering is disabled, we still need to render the file path.
    #            This is because we always render folder names - so the file wouldn't end up in the correct location
    #            within the incarnation.
    path_template = environment.from_string(str(relative_template_path))
    rendered_path = Path(await path_template.render_async(**template_data))

    logger.debug(
        "rendering file in incarnation",
        content_rendered=render_content,
        path=rendered_path,
    )

    template_file_stat = template_file_path.stat(follow_symlinks=False)  # type: ignore
    incarnation_file_path = AsyncPath(incarnation_root_dir, rendered_path)
    await incarnation_file_path.parent.mkdir(parents=True, exist_ok=True)
    if render_content:
        await incarnation_file_path.write_text(rendered_content)
    else:
        await incarnation_file_path.write_bytes(rendered_content)
    apply_path_stats(Path(incarnation_file_path), template_file_stat)
    return incarnation_file_path


async def render_template_dir(
    environment: SandboxedEnvironment,
    template_dir_path: Path,
    incarnation_root_dir: Path,
    template_data: TemplateData,
) -> Path:
    """Render a template directory path into an incarnation directory path."""
    loader: FileSystemLoader = typing.cast(FileSystemLoader, environment.loader)
    relative_template_dir_path = template_dir_path.relative_to(loader.searchpath[0])

    # get and render template file path
    path_template = environment.from_string(str(relative_template_dir_path))
    rendered_path = Path(await path_template.render_async(**template_data))

    logger.debug("rendering directory in incarnation", path=rendered_path)

    template_dir_stat = template_dir_path.stat(follow_symlinks=False)  # type: ignore
    incarnation_dir_path = AsyncPath(incarnation_root_dir, rendered_path)
    await incarnation_dir_path.mkdir(parents=True, exist_ok=True)
    apply_path_stats(Path(incarnation_dir_path), template_dir_stat)
    return incarnation_dir_path


async def render_template_symlink(
    environment: SandboxedEnvironment,
    template_symlink_path: Path,
    incarnation_root_dir: Path,
    template_data: TemplateData,
) -> Path:
    """Render a template symlink path into an incarnation symlink path."""
    loader: FileSystemLoader = typing.cast(FileSystemLoader, environment.loader)
    relative_template_symlink_path = template_symlink_path.relative_to(loader.searchpath[0])

    # get and render template file path
    path_template = environment.from_string(str(relative_template_symlink_path))
    rendered_path = Path(await path_template.render_async(**template_data))
    # get and render template symlink target
    symlink_target_template = environment.from_string(str(template_symlink_path.readlink()))
    rendered_symlink_target_path = Path(await symlink_target_template.render_async(**template_data))

    logger.debug(
        "rendering symlink in incarnation",
        source_path=rendered_path,
        target_path=rendered_symlink_target_path,
    )

    template_symlink_stat = template_symlink_path.stat(follow_symlinks=False)  # type: ignore
    incarnation_symlink_path = incarnation_root_dir / rendered_path
    incarnation_symlink_path.parent.mkdir(parents=True, exist_ok=True)
    incarnation_symlink_path.symlink_to(rendered_symlink_target_path)
    apply_path_stats(incarnation_symlink_path, template_symlink_stat)
    return incarnation_symlink_path


def apply_path_stats(path: Path, target_stat: os.stat_result) -> None:
    """Apply the stats obtained from one path to another path.

    Insights:

        fengine mainly operates within Git repositories.
        Git doesn't store information about the owners and also ONLY
        tracks the executable bit of a UNIX file permissions, meaning that
        only the modes `100755` and `100644` are supported.

        However, this function still applies the entire mode (reported by `stat`),
        to keep things simple.
        It also doesn't affect the ownership of the file.

    This function doesn't follow symlinks.
    """
    chmod = functools.partial(path.chmod, target_stat.st_mode)
    if path.is_symlink():
        try:
            chmod(follow_symlinks=False)
        except NotImplementedError:
            # NOTE(TF): some UNIX platforms (like Linux) don't allow to change permissions
            #           on symlinks. They ALWAYS get 0o777.
            #           Thus, we don't do nothing here.
            pass
    else:
        chmod()
