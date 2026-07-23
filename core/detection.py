from dataclasses import dataclass


@dataclass
class Detection:
    """
    Internal BlurGPT detection format.

    This class isolates the rest of the project from
    the object detector implementation (Ultralytics).
    """

    cls: int

    x1: float
    y1: float
    x2: float
    y2: float