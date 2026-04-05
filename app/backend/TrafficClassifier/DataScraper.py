import time
import numpy as np
from collections import defaultdict
from scapy.all import sniff, IP, TCP, UDP, get_if_addr

class PacketSniffer:
    def __init__(self, interface: str, packet_callback, window_size=8):
        self.interface = interface
        self.packet_callback = packet_callback
        self._running = False
        self.window_size = window_size
        
        try:
            self.local_ip = get_if_addr(interface)
        except:
            self.local_ip = "127.0.0.1"

        self.flows = defaultdict(list)

    def start(self):
        """This was the missing method causing your AttributeError!"""
        self._running = True
        print(f"[*] Flow Scraper started on {self.interface} (Local: {self.local_ip})")
        sniff(
            iface=self.interface,
            prn=self.packet_callback,
            stop_filter=lambda x: not self._running,
            store=0
        )

    def stop(self):
        self._running = False

    def extract_features(self, *args):
        # Extract the packet (handles the 'self' mismatch we discussed)
        packet = args[-1]
        if not packet.haslayer(IP): return None

        # 5-Tuple Extraction
        proto = packet[IP].proto
        src, dst = packet[IP].src, packet[IP].dst
        sport = packet.sport if packet.haslayer(TCP) or packet.haslayer(UDP) else 0
        dport = packet.dport if packet.haslayer(TCP) or packet.haslayer(UDP) else 0
        flow_key = (src, dst, sport, dport, proto)

        self.flows[flow_key].append({
            'len': len(packet),
            'time': time.time(),
            'is_up': src == self.local_ip,
            'sport': sport,
            'dport': dport
        })

        if len(self.flows[flow_key]) >= self.window_size:
            features = self._calculate_54_features(self.flows[flow_key], proto)
            del self.flows[flow_key]
            return features
        
        return None

    def _calculate_54_features(self, flow_data, proto):
            """Calculates stats safely to avoid NumPy truthiness and math errors."""
            
            def get_stats(data):
                # Use len() check because 'if data:' fails if data is an array
                if len(data) == 0: return [0.0] * 8
                
                # Convert to NumPy array immediately for safe math
                arr = np.array(data).astype(float)
                med = np.median(arr)
                
                return [
                    float(np.min(arr)), float(np.max(arr)), float(np.mean(arr)),
                    float(np.median(np.abs(arr - med))), # MAD: array - scalar works now
                    float(np.std(arr)), float(np.percentile(arr, 25)),
                    float(med), float(np.percentile(arr, 75))
                ]

            # 1. Segregate data
            up = [p for p in flow_data if p['is_up']]
            down = [p for p in flow_data if not p['is_up']]
            
            # 2. Extract sequences
            up_lens = [p['len'] for p in up]
            down_lens = [p['len'] for p in down]
            bi_lens = [p['len'] for p in flow_data]
            
            # Inter-Arrival Times (IAT)
            up_times = [p['time'] for p in up]
            down_times = [p['time'] for p in down]
            bi_times = [p['time'] for p in flow_data]
            
            up_iats = np.diff(up_times) if len(up_times) > 1 else []
            down_iats = np.diff(down_times) if len(down_times) > 1 else []
            bi_iats = np.diff(bi_times) if len(bi_times) > 1 else []

            # 3. Assemble the 54 Features
            f = []
            f.extend(get_stats(up_lens))   # 0-7
            f.extend(get_stats(up_iats))   # 8-15
            f.extend(get_stats(down_lens)) # 16-23
            f.extend(get_stats(down_iats)) # 24-31
            f.extend(get_stats(bi_lens))   # 32-39
            f.extend(get_stats(bi_iats))   # 40-47
            
            # 48: Transport Code (0:TCP, 1:UDP, 2:Other)
            f.append(0.0 if proto == 6 else (1.0 if proto == 17 else 2.0))
            # 49: Upstream packet count
            f.append(float(len(up)))
            
            # 50-53: Port Flags
            f.append(1.0 if any(p['dport'] == 443 for p in up) else 0.0) 
            f.append(1.0 if any(p['dport'] == 80 for p in up) else 0.0)  
            f.append(1.0 if any(p['sport'] == 443 for p in down) else 0.0) 
            f.append(1.0 if any(p['sport'] == 80 for p in down) else 0.0)  

            return f