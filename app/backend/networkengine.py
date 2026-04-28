import threading
import time
from typing import Dict, Optional
from backend.engineblueprint import NetworkEngineProvider
from .TrafficClassifier.TrafficClassifier import TrafficClassifier
from scapy.all import get_working_if, conf
import queue
from backend.TrafficClassifier.DataScraper import PacketSniffer

class NetworkEngine(NetworkEngineProvider):
    
    def __init__(self, model_path: str, encoder_path: str, interface: Optional[str] = None) :
        
        self.interface = self._determine_interface(interface)
        
        self.classifier = TrafficClassifier(model_path, encoder_path, interface)
        
        self.scraper = PacketSniffer(self.interface, self.handle_data)
        self.data_lock = threading.Lock()
        self.packet_queue = queue.Queue()
        
        # 2. State management
        self._running = False
        self._thread = None
        
        # 3. The Data Storage
        self.labelcount = {
            "GAME": 0,
            "INSTANT-MESSAGE": 0,
            "MAIL-SERVICE": 0,
            "NETWORK-STORAGE": 0,
            "NETWORK-TRANSMISSION": 0,
            "VIDEO": 0,
            "WEB-BROWSING": 0,
        }
        self.conversations: Dict[str, list] = {k: [] for k in self.labelcount}
        self._MAX_CONVERSATIONS = 50

    def start(self) -> None:
        """Starts the packet processing loop in a background thread."""
        if self._running:
            print("Engine is already running.")
            return

        print("Starting Network Engine...")
        self._running = True
        
        self.sniffer_thread = threading.Thread(target=self.scraper.start, daemon=True)
        self.sniffer_thread.start()
    
        # We run the loop in a separate thread so FastAPI can keep serving the UI
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        


    def stop(self) -> None:
        """Signals the background loop to stop gracefully."""
        print("Stopping Network Engine...")
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            
    def handle_data(self, packet):
        res = self.scraper.extract_features(packet)
        if res is not None:
            features, metadata = res
            if features is not None:
                self.packet_queue.put((features, metadata))

    def ReturnConversations(self, label: str) -> list:
        return list(reversed(self.conversations.get(label.upper(), [])))

    def ReturnLabelcount(self) -> Dict[str, int]:
        """Returns the current classification tally."""
        return self.labelcount.copy()

    def _run_loop(self):
        """The actual background work happens here."""
        while self._running:
            # 1. Capture/Extract Features 
            # (Replace this with your real sniffer logic later)
            try:
                features, metadata = self.packet_queue.get(timeout=1.0)
                
                # 2. Run the ML Prediction
                label,confidence = self.classifier.get_prediction_with_threshold(features)
                label = label.upper() # Standardize to match our dict keys
                
                # 3. Update the counts
                if label in self.labelcount:
                    self.labelcount[label] += 1
                    print(f"[ENGINE] Classified {label} ({confidence:.2f}) - Total: {self.labelcount[label]}")
                    entry = {**metadata, "confidence": round(confidence, 3)}
                    convs = self.conversations[label]
                    convs.append(entry)
                    if len(convs) > self._MAX_CONVERSATIONS:
                        convs.pop(0)
                else:
                    print(f"[ENGINE] Warning: Label '{label}' not in labelcount dictionary.")

                time.sleep(0.5)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[*] Unexpected error in worker: {e}")
                break
                
    def _determine_interface(self, provided_iface: Optional[str]) -> str:
        """Logic to find the best network interface."""
        if provided_iface:
            print(f"[*] Using manually specified interface: {provided_iface}")
            return provided_iface
        
        try:
            # Scapy magic: finds the interface used for the default gateway
            auto_iface = get_working_if().name
            print(f"[*] Auto-detected active interface: {auto_iface}")
            return auto_iface
        except Exception as e:
            # Fallback to whatever Scapy thinks is default
            fallback = conf.iface
            print(f"[!] Auto-detection failed ({e}). Falling back to: {fallback}")
            return str(fallback)