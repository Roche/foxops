from foxops.models.desired_incarnation_state import DesiredIncarnationState
from foxops.models.incarnation import Incarnation


def incarnation_identifier(x: Incarnation | DesiredIncarnationState) -> str:
    return f"{x.incarnation_repository}:{x.target_directory}"
