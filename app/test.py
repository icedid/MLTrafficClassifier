import threading
import time
import queue
import joblib
import numpy as np
from collections import defaultdict
from typing import Optional
from scapy.all import sniff, IP, TCP, UDP, get_working_if, conf, get_if_addr
from scipy.stats import median_abs_deviation

class TrafficClassifier:
    def __init__(self, model_path: str, encoder_path: str):
        self.model = joblib.load(model_path)
        self.encoder = joblib.load(encoder_path)
        print(f"[*] Successfully loaded ML assets.")

    def get_prediction(self, feature_vector: list):
        data = np.array(feature_vector).reshape(1, -1)
        probabilities = self.model.predict_proba(data)[0]
        max_prob = np.max(probabilities)
        prediction_numeric = np.argmax(probabilities)
        label = self.encoder.inverse_transform([prediction_numeric])[0]
        return str(label), float(max_prob)

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
        remote_ip = dst if src == self.local_ip else src
        
        # Filter out local intranet noise (192.168.x.x to 192.168.x.x)
        if src.startswith('192.168.') and dst.startswith('192.168.'):
            return
            
        proto = packet[IP].proto
        sport = packet.sport if packet.haslayer(TCP) or packet.haslayer(UDP) else 0
        dport = packet.dport if packet.haslayer(TCP) or packet.haslayer(UDP) else 0

        ip_pair = tuple(sorted([src, dst]))
        port_pair = tuple(sorted([sport, dport]))
        session_key = (ip_pair, port_pair, proto)

        if session_key in self.completed_sessions:
            return

        is_up = src == self.local_ip
        self.sessions[session_key].append({
            'len': len(packet),
            'time': float(packet.time),
            'is_up': is_up,
            'sport': sport,
            'dport': dport
        })
        
        count = len(self.sessions[session_key])
        
        if count == 8:
            # Calculate diagnostic avg length
            avg_len = sum(p['len'] for p in self.sessions[session_key]) / 8.0
            
            features = self._calculate_54_features(self.sessions[session_key], proto)
            
            # Pass remote_ip, proto, avg_len, and features to the queue
            self.engine_callback((remote_ip, proto, avg_len, features))
            
            self.completed_sessions.add(session_key)
            del self.sessions[session_key]

    def _feature_calculate_exact(self, stream_list):
        pkt_count = len(stream_list)
        if pkt_count == 0:
            return np.zeros((8, 2)), 0
            
        stream = np.array(stream_list)
        if pkt_count > 1:
            stream[:, 0] = np.r_[0, np.diff(np.abs(stream[:, 0])).astype(float)]
        else:
            stream[:, 0] = np.array([0.0])
            
        stream = stream.astype(float)
        stats = np.vstack([
            np.percentile(stream, np.linspace(0., 100., 5), axis=0),
            np.mean(stream, axis=0),
            np.std(stream, axis=0),
            median_abs_deviation(stream, axis=0)
        ])
        return stats, pkt_count

    def _calculate_54_features(self, session_data, proto):
        bistream = [[p['time'], p['len']] for p in session_data]
        upstream = [[p['time'], p['len']] for p in session_data if p['is_up']]
        downstream = [[p['time'], p['len']] for p in session_data if not p['is_up']]

        bi_stats, _ = self._feature_calculate_exact(bistream)
        up_stats, up_pkt_count = self._feature_calculate_exact(upstream)
        down_stats, _ = self._feature_calculate_exact(downstream)

        flow_proto = 0 if proto == 6 else (1 if proto == 17 else 2)

        up_ports, down_ports = [], []
        for p in session_data:
            if p['is_up']: up_ports.extend([p['sport'], p['dport']])
            else: down_ports.extend([p['sport'], p['dport']])
                
        up_443, up_80 = up_ports.count(443), up_ports.count(80)
        down_443, down_80 = down_ports.count(443), down_ports.count(80)

        features = np.r_[
            np.hstack([bi_stats, up_stats, down_stats]).ravel(),
            up_pkt_count, up_443, up_80, down_443, down_80, flow_proto
        ]
        return features.tolist()

class NetworkEngine:
    def __init__(self, model_path: str, encoder_path: str):
        self.interface = get_working_if().name
        self.local_ip = get_if_addr(self.interface)
            
        print(f"[*] Engine bound to: {self.interface} ({self.local_ip})")
        
        self.classifier = TrafficClassifier(model_path, encoder_path)
        self.packet_queue = queue.Queue()
        self.manager = ScraperManager(self.handle_features, self.local_ip)
        self._running = False

    def start(self):
        self._running = True
        self.sniffer_thread = threading.Thread(target=lambda: sniff(
            iface=self.interface, 
            prn=self.manager.process_packet, 
            stop_filter=lambda x: not self._running, 
            store=0
        ), daemon=True)
        self.sniffer_thread.start()
    
        self._logic_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._logic_thread.start()

    def handle_features(self, payload):
        self.packet_queue.put(payload)

    def _run_loop(self):
        import warnings
        warnings.filterwarnings("ignore", category=UserWarning) # Suppress feature names warning
        
        print(f"{'IP ADDRESS':<16} | {'PROTO':<5} | {'PREDICTION':<20} | {'CONF':<5} | {'AVG SIZE'}")
        print("-" * 70)
        
        while self._running:
            try:
                # Unpack the diagnostic payload
                remote_ip, proto, avg_len, features = self.packet_queue.get(timeout=1.0)
                label, confidence = self.classifier.get_prediction(features)
                
                proto_str = "UDP" if proto == 17 else "TCP" if proto == 6 else "OTH"
                
                print(f"{remote_ip:<16} | {proto_str:<5} | {label.upper():<20} | {confidence:.2f}  | {avg_len:>5.0f} B")
                
            except queue.Empty:
                continue

if __name__ == "__main__":
    MODEL_PATH = "traffic_classifier_lgbm.pkl"
    ENCODER_PATH = "label_encoder.pkl"

    try:
        engine = NetworkEngine(MODEL_PATH, ENCODER_PATH)
        engine.start()
        print("[*] Sniffing active. Press CTRL+C to stop.\n")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        engine._running = False