import time
import numpy as np
from collections import defaultdict
from scapy.all import sniff, IP, TCP, UDP, get_if_addr
from scipy.stats import median_abs_deviation

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
        # FIX 1: Added session lock to ensure each flow is only classified once
        self.completed_sessions = set()

    def start(self):
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
        # Handle the Scapy callback argument correctly
        packet = args[-1]
        if not packet.haslayer(IP): return None, None

        src, dst = packet[IP].src, packet[IP].dst
        
        # FIX 2: Added intranet noise filtering
        if src.startswith('192.168.') and dst.startswith('192.168.'):
            return None, None

        proto = packet[IP].proto
        sport = packet.sport if packet.haslayer(TCP) or packet.haslayer(UDP) else 0
        dport = packet.dport if packet.haslayer(TCP) or packet.haslayer(UDP) else 0

        # FIX 3: Implemented bidirectional flow key using sorted tuples
        ip_pair = tuple(sorted([src, dst]))
        port_pair = tuple(sorted([sport, dport]))
        flow_key = (ip_pair, port_pair, proto)

        # Ensure we don't re-process a completed session
        if flow_key in self.completed_sessions:
            return None, None

        self.flows[flow_key].append({
            'len': len(packet),
            'time': float(packet.time), # Use precise packet timestamp
            'is_up': src == self.local_ip,
            'sport': sport,
            'dport': dport
        })

        if len(self.flows[flow_key]) >= self.window_size:
            features = self._calculate_54_features(self.flows[flow_key], proto)
            
            metadata = {
                "src": src, "dst": dst, 
                "sport": sport, "dport": dport, 
                "proto": "TCP" if proto == 6 else ("UDP" if proto == 17 else str(proto))
            }
            
            # Lock the session and clean up memory
            self.completed_sessions.add(flow_key)
            del self.flows[flow_key]
            return features, metadata
        
        return None, None

    def _feature_calculate_exact(self, stream_list):
        """Calculates interleaved stats for Time and Length exactly as in test.py."""
        pkt_count = len(stream_list)
        if pkt_count == 0:
            return np.zeros((8, 2)), 0
            
        stream = np.array(stream_list)
        # Apply IAT calculation and pad first packet with 0
        if pkt_count > 1:
            stream[:, 0] = np.r_[0, np.diff(np.abs(stream[:, 0])).astype(float)]
        else:
            stream[:, 0] = np.array([0.0])
            
        stream = stream.astype(float)
        # Vertical stack of percentiles, mean, std, and MAD
        stats = np.vstack([
            np.percentile(stream, np.linspace(0., 100., 5), axis=0),
            np.mean(stream, axis=0),
            np.std(stream, axis=0),
            median_abs_deviation(stream, axis=0)
        ])
        return stats, pkt_count

    def _calculate_54_features(self, flow_data, proto):
        """Assembles the 54-feature vector in the correct Bi->Up->Down order."""
        bistream = [[p['time'], p['len']] for p in flow_data]
        upstream = [[p['time'], p['len']] for p in flow_data if p['is_up']]
        downstream = [[p['time'], p['len']] for p in flow_data if not p['is_up']]

        bi_stats, _ = self._feature_calculate_exact(bistream)
        up_stats, up_pkt_count = self._feature_calculate_exact(upstream)
        down_stats, _ = self._feature_calculate_exact(downstream)

        # Transport code: 0 for TCP, 1 for UDP, 2 for Other
        flow_proto = 0 if proto == 6 else (1 if proto == 17 else 2)

        up_ports, down_ports = [], []
        for p in flow_data:
            if p['is_up']: up_ports.extend([p['sport'], p['dport']])
            else: down_ports.extend([p['sport'], p['dport']])
                
        up_443, up_80 = up_ports.count(443), up_ports.count(80)
        down_443, down_80 = down_ports.count(443), down_ports.count(80)

        # Assemble final vector using interleaved raveling
        features = np.r_[
            np.hstack([bi_stats, up_stats, down_stats]).ravel(),
            up_pkt_count, up_443, up_80, down_443, down_80, flow_proto
        ]
        return features.tolist()