from abc  import ABC, abstractmethod
from typing import Dict


class NetworkEngineProvider(ABC):
    
    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def stop(self) -> None:
        """Signal the background loop to stop."""
        raise NotImplementedError

    @abstractmethod
    def ReturnLabelcount(self) -> Dict[str,int]:
        raise NotImplementedError