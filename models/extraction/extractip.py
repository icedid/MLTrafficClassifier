import numpy as np
from scapy.all import PcapReader, IP, TCP, UDP
import os
from scipy.stats import median_abs_deviation

# --- 1. The Mathematical Engine ---
def feature_calculate(stream):
    pkt_count = len(stream)
    stream = np.array(stream)
    
    # Calculate Inter-Arrival Time (IAT)
    stream[:, 0] = np.r_[0, np.diff(np.abs(stream[:, 0])).astype(float)]
    stream = stream.astype(float)
    
    # Calculate Stats: 0, 25, 50, 75, 100 percentiles + Mean + Std + MAD
    stats = np.vstack([
        np.percentile(stream, np.linspace(0., 100., 5), 0), 
        np.mean(stream, 0), 
        np.std(stream, 0), 
        median_abs_deviation(stream, 0)
    ])
    return stats, pkt_count

# --- 2. The Fixed Extraction Logic ---
def extract_feature_label_fixed(session_parent_dir):
    labels = []
    flow_features = []
    
    # Filter for valid PCAP files
    session_dir = [f for f in os.listdir(session_parent_dir) if f.endswith(('.pcap', '.pcapng'))]
    user_ip_prefix = ('100.64', '192.168')

    print(f"Starting extraction on {len(session_dir)} files...")

    for pcap_file in session_dir:
        print(f"Processing {pcap_file}...", end=" ", flush=True)
        
        flows = {} 
        label = pcap_file.split('_')[2]
        pcap_path = os.path.join(session_parent_dir, pcap_file)
        
        try:
            with PcapReader(pcap_path) as reader:
                for pkt in reader:
                    # FIX: Explicitly check if IP exists
                    if not pkt.haslayer('IP'): 
                        continue
                    
                    # FIX: Check if Scapy successfully parsed the Transport Layer
                    # Instead of trusting the IP Proto field, we check the layers directly.
                    if pkt.haslayer('TCP'):
                        layer = pkt['TCP']
                        proto = 6
                    elif pkt.haslayer('UDP'):
                        layer = pkt['UDP']
                        proto = 17
                    else:
                        continue # Skip packets that are IP but not parsed as TCP/UDP
                        
                    # --- SESSIONIZATION STEP ---
                    # Create a canonical Key (Sort IPs and Ports)
                    ip_pair = tuple(sorted((pkt['IP'].src, pkt['IP'].dst)))
                    port_pair = tuple(sorted((layer.sport, layer.dport)))
                    flow_id = ip_pair + port_pair + (proto,)
                    
                    if flow_id not in flows:
                        flows[flow_id] = {
                            'bi': [], 'up': [], 'dn': [], 
                            'up_ports': [], 'dn_ports': []
                        }
                    
                    # --- THE "FIRST 8" RULE ---
                    if len(flows[flow_id]['bi']) < 8:
                        pkt_data = [float(pkt.time), len(pkt)]
                        flows[flow_id]['bi'].append(pkt_data)
                        
                        if pkt['IP'].src.startswith(user_ip_prefix):
                            flows[flow_id]['up'].append(pkt_data)
                            flows[flow_id]['up_ports'].extend([layer.sport, layer.dport])
                        else:
                            flows[flow_id]['dn'].append(pkt_data)
                            flows[flow_id]['dn_ports'].extend([layer.sport, layer.dport])

            # --- PROCESS FLOWS FOR THIS FILE ---
            file_flow_count = 0
            for f_id, data in flows.items():
                if len(data['bi']) < 3: continue
                
                # Calculate features (Same as before)
                bi_s, _ = feature_calculate(data['bi'])
                
                if len(data['up']) > 0:
                    up_s, up_pkt_count = feature_calculate(data['up'])
                else:
                    up_s = np.zeros((8, 2))
                    up_pkt_count = 0
                
                if len(data['dn']) > 0:
                    dn_s, _ = feature_calculate(data['dn'])
                else:
                    dn_s = np.zeros((8, 2))
                
                up_p_443 = data['up_ports'].count(443)
                up_p_80 = data['up_ports'].count(80)
                dn_p_443 = data['dn_ports'].count(443)
                dn_p_80 = data['dn_ports'].count(80)
                fl_proto = 0 if f_id[4] == 6 else 1 

                combined = np.r_[
                    np.hstack([bi_s, up_s, dn_s]).ravel(), 
                    up_pkt_count, 
                    [up_p_443, up_p_80], 
                    [dn_p_443, dn_p_80], 
                    fl_proto
                ]
                
                flow_features.append(combined)
                labels.append(label)
                file_flow_count += 1
            
            print(f"Done. Extracted {file_flow_count} flows.")
            
        except Exception as e:
            print(f"Error reading {pcap_file}: {e}")
            continue

    if not flow_features:
        print("No features extracted.")
        return np.array([]), np.array([])

    flow_features = np.vstack(flow_features)
    labels = np.array(labels)
    
    # Normalization
    flow_features = (flow_features - flow_features.min(0)) / (flow_features.max(0) - flow_features.min(0) + 1e-4)
    
    return flow_features, labels

if __name__ == "__main__":
    input_folder = '/kaggle/input/onu-capture' 
    output_folder = '/kaggle/working/session_extracted'
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    print("Starting Flow-Level Extraction...")
    X, y = extract_feature_label_fixed(input_folder)
    
    if len(y) > 0:
        np.save(os.path.join(output_folder, 'flow_features.npy'), X)
        np.save(os.path.join(output_folder, 'labels.npy'), y)
        print(f"Success! Saved {len(y)} samples.")
