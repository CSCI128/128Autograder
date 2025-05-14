import abc

class ITransformer(abc.ABC):
    @abc.abstractmethod
    def transform(self, string: str) -> str:
        raise NotImplementedError()
