https://www.nature.com/articles/s41597-025-04876-2
### **Core Objective & Methodology**

- **Purpose**: The dataset is designed to identify latent traffic patterns and improve network management by providing authentic data on network scales, user behaviors, and spatial-temporal characteristics.
    
- **Collection Platforms**: Data was sourced from two primary platforms: **BRAS** (Broadband Remote Access Server) access devices and **ONU** (Optical Network Unit) edge devices.
    
- **Scale**: The collection involved nearly 46,000 active users (19.5k for BRAS; 26.4k for ONU) in a prefecture-level city, capturing bidirectional traffic peaks of 45 Gbit/s.
    
- **Dual-Technology Approach**: It combines **Deep Packet Inspection (DPI)** for high-accuracy labeling of non-encrypted traffic (up to 95%) and **Deep Flow Inspection (DFI)** to identify encrypted and unknown traffic using machine learning.
    

### **Feature Engineering & Processing**

- **The "First 8" Rule**: To optimize real-time performance and resource usage, the researchers determined that extracting features from only the **first 8 packets** of each flow is the most efficient window for high classification accuracy.
    
- **Feature Categories**: A total of **54 features** are extracted for each session, including:
    
    - **Dimensional Features**: The 5-tuple (source/destination IP, ports, and protocol).
        
    - **Statistical Features**: Minimum, maximum, mean, median absolute deviation (MAD), standard deviation, median (p50), 25th percentile, and 75th percentile for both packet lengths and inter-arrival times (IAT).
        
    - **Label Features**: Application categories like video, gaming, and instant messaging.
        

### **Application Classification**

- **Standardized Labels**: The dataset uses seven major application categories for model output: network-storage, network-transmission, video, game, instant-messaging, mail-service, and web-browsing.
    
- **Technical Validation**: The dataset's quality was verified against the ISCXVPN2016 dataset, showing over 99% TCP stream integrity and extremely low UDP packet loss rates (below 0.05%).
    
- **Accuracy**: Using lightweight machine learning models like Random Forest, the researchers achieved classification identification accuracy exceeding 95%.