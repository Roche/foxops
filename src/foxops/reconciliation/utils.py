import hashlib

from tenacity import retry, retry_if_exception_type, stop_after_attempt

from foxops.errors import RetryableError

retry_if_possible = retry(
    retry=retry_if_exception_type(RetryableError),
    # NOTE: "why retry 4 times?" ... well, go figure ;)
    stop=stop_after_attempt(4),
)


def generate_foxops_branch_name(prefix: str, target_directory: str, template_repository_version: str) -> str:
    target_directory_hash = hashlib.sha1(target_directory.encode("utf-8")).hexdigest()[:7]
    return f"foxops/{prefix}-{target_directory_hash}-{template_repository_version}"
