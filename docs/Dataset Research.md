#MLPart

## **1. CESNET-QUIC22** [Zenodo][](https://pmc.ncbi.nlm.nih.gov/articles/PMC12059165/)​

- **153 million QUIC flows** collected Oct-Nov 2022 on real ISP backbone (CESNET2, 100 Gbps)
    
- **CSV format** with packet metadata sequences (first 30 packets)
    
- **IAT features**: Inter-packet times in milliseconds (sequence + 8-bin histogram)
    
- **Packet length**: Byte sizes in sequence and histogram format
    
- **Labels**: 102 QUIC application classes + background traffic
    
- **89 GB uncompressed**; Python library support (cesnet-datazoo)
    

## **2. CESNET-TLS-Year22** [Zenodo, Nature Scientific Data 2024][](https://arxiv.org/pdf/2601.04089.pdf)​

- **Full calendar year 2022** of TLS traffic on real ISP backbone
    
- **180 web services** with 24 traffic categories
    
- **Packet sequences**: First 30 packets with IAT, packet sizes, directions
    
- **Histograms**: 8 logarithmic bins for inter-packet times and packet sizes
    
- **TLS ClientHello fields**: SNI, cipher suites, protocol versions
    
- Comprehensive year-long baseline for TLS 1.3 classification
    

## **3. A Real Network Environment Dataset for Traffic Analysis** [figshare, 2025][](https://www.nature.com/articles/s41597-025-04603-x)​

- **10.4 GB** from real ISP network (19,417 users, 45 Gbps peak traffic)
    
- **54 CSV statistical features** including:
    
    - Packet inter-arrival time (TΔ): min, max, mean, MAD, std, p25, p50, p75
        
    - Packet length (LΔ): identical statistical aggregates
        
    - Protocol encoding and directional variants
        
- **9 application categories** (web-browsing, video, games, instant messaging, etc.)
    
- **Hybrid DPI/DFI labeling** with 95%+ accuracy for encrypted traffic
    
- First 8 packets per flow (optimized for real-time deployment)
    

## **4. CipherSpectrum** [UNSW, IEEE S&P 2025][](https://www.sciencedirect.com/science/article/pii/S0360835225001871)​

- **120,000 TLS 1.3 sessions** collected Jan-Mar 2024
    
- **3 AEAD cipher suites** (TLS-AES-128-GCM, TLS-AES-256-GCM, TLS-CHACHA20-POLY1305)
    
- **40 domains** with equal representation across classes and suites
    
- Addresses **cipher-agnostic classification** problem for modern TLS 1.3
    
- Balanced dataset design avoiding sampling bias
    

---

## **TIER 2: GOOD MATCHES**

## **5. VisQUIC** [arXiv 2025][](https://github.com/wangtz19/Awesome-NTA)​

- 100,000+ labeled QUIC flows, recent 2025 publication
    
- Limited published details (under peer review)
    

## **6. CESNET-TimeSeries24** [Zenodo, Nature Scientific Data 2025][](https://rke.abertay.ac.uk/files/101106478/Al-Jobouri_ImplementingPacket-LevelInternet_Published_2025.pdf)​

- Aggregated time-series from 66 billion IP flows, 3.7 petabytes
    
- Real ISP network context for encrypted traffic trends