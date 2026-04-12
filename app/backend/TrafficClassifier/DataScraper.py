from scapy.all import sniff
import numpy as np
from collections import defaultdict
from scapy.all import IP, TCP, UDP


class DataScraper:
    def __init__(self, interface: str, packet_callback):
        """
        A pure sniffer. 
        :param interface: The network interface to listen on (e.g., 'eth0').
        :param packet_callback: The function to call for every captured packet.
        """
        self.interface = interface
        self.packet_callback = packet_callback
        self._running = False
        
    def start(self):
        self._running = True
        print(f"[*] DataScraper started on interface: {self.interface}")
        
        # store=0 is CRITICAL here. If it defaults to 1, Scapy will keep 
        # every packet in RAM until your machine crashes.
        sniff(
            iface=self.interface, 
            prn=self.packet_callback, 
            stop_filter=lambda x: not self._running, 
            store=0
        )

    def stop(self):
        print("[*] Stopping DataScraper...")
        self._running = False
        

class ScraperManager:
    def __init__(self, engine_callback, local_ip: str):
        """
        Manages sessions and generates ML features.
        :param engine_callback: The function to call when a 54-feature vector is ready.
        :param local_ip: Used to determine Upstream vs Downstream.
        """
        self.engine_callback = engine_callback
        self.local_ip = local_ip
        
        # Active sessions waiting to hit 8 packets
        self.sessions = defaultdict(list)
        
        # Track completed sessions so we ignore packets 9, 10, etc.
        self.completed_sessions = set() 

    def process_packet(self, packet):
        """The callback triggered by DataScraper for every packet."""
        if not packet.haslayer(IP):
            return

        # 1. IDENTIFY THE SESSION (Bidirectional Key)
        src, dst = packet[IP].src, packet[IP].dst
        proto = packet[IP].proto
        sport = packet.sport if packet.haslayer(TCP) or packet.haslayer(UDP) else 0
        dport = packet.dport if packet.haslayer(TCP) or packet.haslayer(UDP) else 0

        # Sort IPs and Ports so (A->B) and (B->A) map to the same session bucket
        ip_pair = tuple(sorted([src, dst]))
        port_pair = tuple(sorted([sport, dport]))
        session_key = (ip_pair, port_pair, proto)

        # 2. ENFORCE "FIRST 8" RULE
        if session_key in self.completed_sessions:
            return

        # 3. STORE REQUIRED METRICS
        # Note: We use packet.time (hardware timestamp) instead of time.time()
        # and multiply by 1000 to get the Milliseconds the model was trained on.
        self.sessions[session_key].append({
            'len': len(packet),
            'time': float(packet.time) * 1000.0, 
            'is_up': src == self.local_ip,
            'sport': sport,
            'dport': dport
        })

        # 4. TRIGGER FEATURE EXTRACTION
        if len(self.sessions[session_key]) == 8:
            # Calculate the 54 features
            features = self._calculate_54_features(self.sessions[session_key], proto)
            
            # Fire the callback to send data to the Engine/ML Model
            self.engine_callback(features)
            
            # Clean up and mark as completed
            self.completed_sessions.add(session_key)
            del self.sessions[session_key]

    def _calculate_54_features(self, session_data, proto):
        """Calculates the 54 features matching the Onu_features.csv exact order."""
        
        def get_stats(data):
            if not data: return [0.0] * 8
            arr = np.array(data)
            med = np.median(arr)
            mad = np.median(np.abs(arr - med))
            
            # Order: min, max, avg, median, 25_per, 75_per, mad, std
            return [
                float(np.min(arr)), float(np.max(arr)), float(np.mean(arr)),
                float(med), float(np.percentile(arr, 25)), float(np.percentile(arr, 75)),
                float(mad), float(np.std(arr))
            ]

        # Segregate direction
        up = [p for p in session_data if p['is_up']]
        down = [p for p in session_data if not p['is_up']]

        # 1. Packet Lengths
        up_lens = [p['len'] for p in up]
        down_lens = [p['len'] for p in down]
        bi_lens = [p['len'] for p in session_data]

        # 2. Inter-Arrival Times (IAT)
        up_iats = np.diff([p['time'] for p in up]) if len(up) > 1 else []
        down_iats = np.diff([p['time'] for p in down]) if len(down) > 1 else []
        bi_iats = np.diff([p['time'] for p in session_data]) if len(session_data) > 1 else []

        # 3. Build the array
        f = []
        f.extend(get_stats(up_lens))   # 0-7
        f.extend(get_stats(up_iats))   # 8-15
        f.extend(get_stats(down_lens)) # 16-23
        f.extend(get_stats(down_iats)) # 24-31
        f.extend(get_stats(bi_lens))   # 32-39
        f.extend(get_stats(bi_iats))   # 40-47
        
        # 48. Transport Protocol (TCP=0, UDP=1, Other=2)
        f.append(0.0 if proto == 6 else (1.0 if proto == 17 else 2.0))
        
        # 49. Uplink Packet Count
        f.append(float(len(up)))
        
        # 50-53. Specific Port Counts (Not boolean flags)
        f.append(float(sum(1 for p in up if p['dport'] == 443)))
        f.append(float(sum(1 for p in up if p['dport'] == 80)))
        f.append(float(sum(1 for p in down if p['sport'] == 443)))
        f.append(float(sum(1 for p in down if p['sport'] == 80)))

        return f