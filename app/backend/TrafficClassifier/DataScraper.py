from scapy.all import sniff, IP

class PacketSniffer:
    def __init__(self, interface: str, packet_callback):
        self.interface = interface
        self.packet_callback = packet_callback # This is the function it will 'ping'
        self._running = False

    def start(self):
        self._running = True
        print(f"[*] Sniffer started on {self.interface}")
        sniff(
            iface=self.interface,
            prn=self.packet_callback, # Every packet goes to the Engine's method
            stop_filter=lambda x: not self._running,
            store=0
        )

    def stop(self):
        self._running = False

    def extract_features(self, *args):
        # Example: Pulling raw data from the IP layer
        packet = args[-1]
        
        if packet.haslayer(IP):
            return [
                len(packet),           # Feature 1: Length
                packet[IP].ttl,        # Feature 2: TTL
                packet[IP].proto,      # Feature 3: Protocol ID
                # Add more to match your model's training requirements
            ]
        return None