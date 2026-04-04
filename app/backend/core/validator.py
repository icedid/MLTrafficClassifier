from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List

@dataclass
class ValidationResult:
    """Standardized response for all system checks."""
    success: bool
    message: str = ""

class BaseValidator(ABC):
    """The Interface: All validators must follow this contract."""
    
    @abstractmethod
    def is_valid(self, targets: List[str]) -> ValidationResult:
        """Must return a ValidationResult object."""
        pass

class MLAssetValidator(BaseValidator):
    """Concrete implementation to catch LFS pointers and missing files."""
    
    def is_valid(self, targets: List[str]) -> ValidationResult:
        for path_str in targets:
            path = Path(path_str)
            
            # 1. Existence Check
            if not path.exists():
                return ValidationResult(False, f"Missing file: {path_str}")
            
            # 2. LFS Pointer Check
            # Git LFS pointers are tiny text files (~130 bytes).
            if path.stat().st_size < 1024:
                try:
                    with open(path, 'r') as f:
                        content = f.read(100)
                        if "version https://git-lfs" in content:
                            return ValidationResult(
                                False, 
                                f"Binary missing! {path.name} is a Git LFS pointer. Run 'git lfs pull'."
                            )
                except (UnicodeDecodeError, PermissionError):
                    # If it's a real binary, reading as 'r' (text) will fail.
                    # This is actually a good sign that it's not a pointer!
                    pass
                        
        return ValidationResult(True, "ML Assets verified.")