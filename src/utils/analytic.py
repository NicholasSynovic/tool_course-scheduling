from abc import ABCMeta, abstractmethod


class Analytic(metaclass=ABCMeta):

    @abstractmethod
    def compute(self): ...

    @abstractmethod
    def plot(self, data): ...

    @abstractmethod
    def run(self) -> None: ...
