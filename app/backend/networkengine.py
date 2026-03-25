import os
import time
import threading
import numpy as np
import joblib
from collections import defaultdict
from backend import NetworkEngineProvider


class NetworkEngine(NetworkEngineProvider):
    
    def __init__(self):
        self.model
        self.labelcount = {
            "GAME": 0,
            "INSTANT-MESSAGE": 0,
            "MAIL-SERVICE": 0,
            "NETWORK-STORAGE": 0,
            "NETWORK-TRANSMISSION": 0,
            "VIDEO": 0,
            "WEB-BROWSING": 0,
        }
        
        
        
    def ReturnLabelcount(self):
        return self.labelcount.copy()