- **Live Sniffing:** Use **Scapy** to listen to the network interface. It captures packet headers while ignoring the private payload to keep the process lightweight.
    
- **Flow Sessionization:** Group packets into "conversations" using the 5-tuple (Source/Dest IP, Source/Dest Port, Protocol).
    
- **The "First 8" Window:** Maintain a buffer for each conversation. Once it hits exactly **8 packets**, it triggers the analysis. Any packets after #8 are ignored for that specific flow to save CPU.
    
- **Feature Extraction:** Calculate the **54 statistical features** from those 8 packets (e.g., Inter-Arrival Times, Packet Size Mean/Std Dev, Forward vs. Backward flow).
    
- **Inference & Recording:** * Feed the 54 features into the `traffic_classifier_rf.pkl`.
    
    - Translate the numeric output (e.g., `0`) into a name (e.g., `"VIDEO"`) using the `label_encoder.pkl`.
        
    - **The Hand-off:** Write that name into a **shared Python dictionary** (e.g., `latest_stats`) so the FastAPI "Reader" can grab it.