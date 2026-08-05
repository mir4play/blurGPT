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

    @property
    def cx(self):
        return (self.x1 + self.x2) / 2

    @property
    def cy(self):
        return (self.y1 + self.y2) / 2

    @property
    def w(self):
        return self.x2 - self.x1

    @property
    def h(self):
        return self.y2 - self.y1

    @property
    def area(self):
        return self.w * self.h

    @property
    def width(self):
        return self.x2 - self.x1


    @property
    def height(self):
        return self.y2 - self.y1


    @property
    def cx(self):
        return (self.x1 + self.x2) / 2


    @property
    def cy(self):
        return (self.y1 + self.y2) / 2