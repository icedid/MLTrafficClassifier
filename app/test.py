import threading
import time
import queue
import joblib
import numpy as np
import pandas as pd
from collections import defaultdict
from typing import Dict, Optional
from scapy.all import sniff, IP, TCP, UDP, get_working_if, conf, get_if_addr

# ==========================================
# 1. THE BRAIN: ML Inference
# ==========================================
class TrafficClassifier:
    def __init__(self, model_path: str, encoder_path: str):
        try:
            self.model = joblib.load(model_path)
            self.encoder = joblib.load(encoder_path)
            print(f"[*] Encoder Classes: {self.encoder.classes_}")
            
            # Feature order based on the Onu_features.csv methodology
            self.feature_names = [
                f"{prefix}_{stat}" 
                for prefix in ["up_pkt_len", "up_pkt_iat", "down_pkt_len", "down_pkt_iat", "bi_pkt_len", "bi_pkt_iat"]
                for stat in ["min", "max", "avg", "median", "25_per", "75_per", "mad", "std"]
            ] + ["transport_code", "up_pkt_num", "https_up_pkt_num", "http_up_pkt_num", "https_down_pkt_num", "http_down_pkt_num"]
            
            print(f"[*] Successfully loaded ML assets: {model_path}, {encoder_path}")
        except Exception as e:
            print(f"[!] Error loading ML assets: {e}")
            raise

    def get_prediction_with_threshold(self, feature_vector: list, threshold: float = 0.6):
        try:
            # 1. Convert to DataFrame (Pass raw features directly)
            data = pd.DataFrame([feature_vector], columns=self.feature_names)

            # Detailed debug print of the input vector
            print("\n" + "-"*30 + " MODEL INPUT START " + "-"*30)
            feature_dict = data.iloc[0].to_dict()
            for k, v in feature_dict.items():
                print(f"{k:<25}: {v}")
            print("-" * 30 + "  MODEL INPUT END  " + "-"*30 + "\n")

            # 2. Inference
            probabilities = self.model.predict_proba(data)[0]
            max_prob = np.max(probabilities)
            prediction_numeric = np.argmax(probabilities)
            
            print(f"DEBUG [Model]: Probabilities: {np.round(probabilities, 3)} | Max: {max_prob:.2f}")
    
            label = self.encoder.inverse_transform([prediction_numeric])[0]

            return str(label), float(max_prob)
        except Exception as e:
            print(f"[!] Inference error: {e}")
            return "Error", 0.0

# ==========================================
# 2. THE MANAGER: Session Logic & Math
# ==========================================
class ScraperManager:
    def __init__(self, engine_callback, local_ip: str):
        self.engine_callback = engine_callback
        self.local_ip = local_ip
        self.sessions = defaultdict(list)
        self.completed_sessions = set() 

    def process_packet(self, packet):
        if not packet.haslayer(IP):
            return

        src, dst = packet[IP].src, packet[IP].dst
        proto = packet[IP].proto
        sport = packet.sport if packet.haslayer(TCP) or packet.haslayer(UDP) else 0
        dport = packet.dport if packet.haslayer(TCP) or packet.haslayer(UDP) else 0

        # Bidirectional Key (Merges Up/Down)
        ip_pair = tuple(sorted([src, dst]))
        port_pair = tuple(sorted([sport, dport]))
        session_key = (ip_pair, port_pair, proto)

        if session_key in self.completed_sessions:
            return

        is_up = src == self.local_ip
        self.sessions[session_key].append({
            'len': len(packet),
            'time': float(packet.time) * 1000.0, # Milliseconds
            'is_up': is_up,
            'sport': sport,
            'dport': dport
        })
        
        # Print packet progress for this specific flow
        count = len(self.sessions[session_key])
        direction = "UP" if is_up else "DOWN"
        print(f"DEBUG [Sniffer]: {src}:{sport} -> {dst}:{dport} [{direction}] | Progress: {count}/8")

        if count == 8:
            print(f"\n[!] Session {session_key} reached 8 packets. Sending to feature extractor...")
            features = self._calculate_54_features(self.sessions[session_key], proto)
            self.engine_callback(features)
            self.completed_sessions.add(session_key)
            del self.sessions[session_key]

    def _calculate_54_features(self, session_data, proto):
        def get_stats(data):
            if len(data) == 0: 
                return [0.0] * 8
            arr = np.array(data)
            med = np.median(arr)
            mad = np.median(np.abs(arr - med))
            return [
                float(np.min(arr)), float(np.max(arr)), float(np.mean(arr)),
                float(med), float(np.percentile(arr, 25)), float(np.percentile(arr, 75)),
                float(mad), float(np.std(arr))
            ]

        up = [p for p in session_data if p['is_up']]
        down = [p for p in session_data if not p['is_up']]

        print(f"DEBUG [Features]: Upstream pkts: {len(up)}, Downstream pkts: {len(down)}")

        up_lens, down_lens, bi_lens = [p['len'] for p in up], [p['len'] for p in down], [p['len'] for p in session_data]
        up_iats = np.diff([p['time'] for p in up]) if len(up) > 1 else []
        down_iats = np.diff([p['time'] for p in down]) if len(down) > 1 else []
        bi_iats = np.diff([p['time'] for p in session_data]) if len(session_data) > 1 else []

        f = []
        f.extend(get_stats(up_lens))   # Upstream Lens
        f.extend(get_stats(up_iats))   # Upstream IAT
        f.extend(get_stats(down_lens)) # Downstream Lens
        f.extend(get_stats(down_iats)) # Downstream IAT
        f.extend(get_stats(bi_lens))   # Bi-directional Lens
        f.extend(get_stats(bi_iats))   # Bi-directional IAT
        
        f.append(0.0 if proto == 6 else (1.0 if proto == 17 else 2.0))
        f.append(float(len(up)))
        f.append(float(sum(1 for p in up if p['dport'] == 443)))
        f.append(float(sum(1 for p in up if p['dport'] == 80)))
        f.append(float(sum(1 for p in down if p['sport'] == 443)))
        f.append(float(sum(1 for p in down if p['sport'] == 80)))

        return f

# ==========================================
# 3. THE ORCHESTRATOR: Engine Pipeline
# ==========================================
class NetworkEngine:
    def __init__(self, model_path: str, encoder_path: str, interface: Optional[str] = None):
        self.interface = self._determine_interface(interface)
        self.local_ip = get_if_addr(self.interface) if self.interface else "127.0.0.1"
            
        print(f"[*] Engine bound to: {self.interface} ({self.local_ip})")
        
        self.classifier = TrafficClassifier(model_path, encoder_path)
        self.packet_queue = queue.Queue()
        
        self.manager = ScraperManager(engine_callback=self.handle_features, local_ip=self.local_ip)
        self._running = False
        self.labelcount = defaultdict(int)

    def start(self):
        self._running = True
        # Sniffer Thread
        print(f"[*] Starting sniffer on {self.interface}...")
        self.sniffer_thread = threading.Thread(target=lambda: sniff(
            iface=self.interface, 
            prn=self.manager.process_packet, 
            stop_filter=lambda x: not self._running, 
            store=0
        ), daemon=True)
        self.sniffer_thread.start()
    
        # Logic Thread
        self._logic_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._logic_thread.start()

    def handle_features(self, features):
        # print("DEBUG [Queue]: Features pushed to logic thread.")
        self.packet_queue.put(features)

    def _run_loop(self):
        while self._running:
            try:
                features = self.packet_queue.get(timeout=1.0)
                label, confidence = self.classifier.get_prediction_with_threshold(features)
                
                self.labelcount[label.lower()] += 1
                print(f"[RESULT] {label.upper():<20} | Confidence: {confidence:.2f}")
                
            except queue.Empty:
                continue

    def _determine_interface(self, provided_iface: Optional[str]) -> str:
        if provided_iface: return provided_iface
        try: return get_working_if().name
        except: return str(conf.iface)

# ==========================================
# 4. POC EXECUTION
# ==========================================
if __name__ == "__main__":
    MODEL_PATH = "traffic_classifier_lgbm.pkl"
    ENCODER_PATH = "label_encoder.pkl"

    try:
        engine = NetworkEngine(MODEL_PATH, ENCODER_PATH)
        engine.start()
        
        print("\n[*] Sniffing active. First 8 packets of each session will be classified.")
        print("[*] Press CTRL+C to stop.\n")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        engine._running = False