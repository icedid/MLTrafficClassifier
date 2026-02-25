from abc  import ABC, abstractmethod

class NetworkEngineProvider(ABC):
    
    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def stop(self) -> None:
        """Signal the background loop to stop."""
        raise NotImplementedError

    @abstractmethod
    def get