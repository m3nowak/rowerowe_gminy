from abc import ABC, abstractmethod


class _RGState(ABC):
    def __init__(self):
        raise NotImplementedError("You probably didn't include overrides in your base App")

    @abstractmethod
    def __setitem__(self, key, value):
        pass

    @abstractmethod
    def __getitem__(self, key):
        pass
