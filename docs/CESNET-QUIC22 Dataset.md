#MLPart 

[[A Real Network Environment Dataset for Traffic Analysis]]
[[PCAP]]

- Tried (https://springernature.figshare.com/articles/dataset/Tracffic_data_from_real_network_environment/28380347) 
- CSV doesn't train properly. most likely corrupt data
- using github (https://github.com/zqxfree/Real-network-datasets-for-application-analysis/tree/main) to rextract pvap files
- script could be wrong. reworking script so that it inteerpreates data correctly
- **Corrected Data Granularity:** Shifted from processing whole PCAP files to isolating individual "conversations" (flows). This transformed a small set of 41 generic files into a robust training set of **25,685 unique samples**.
- **In-Memory Sessionization:** Implemented logic to track unique 5-tuples (Source/Dest IP, Ports, and Protocol) in RAM. This "sorts" raw traffic on the fly, isolating specific application signatures from background network noise.
    
- **Feature Engineering (The "First 8" Rule):** Standardized the extraction of 54 features—including statistical aggregates for Inter-Arrival Time (IAT) and Packet Length—specifically from the first 8 packets of each conversation to capture the initial application "handshake."
    
- **Normalization:** Scaled all extracted metrics to a range between 0.0 and 1.0. This prevents the model from being biased toward features with larger numerical units (like bytes) over smaller ones (like microseconds).
    
- **Training Readiness:** Compiled the features and labels into a structured format compatible with a Random Forest classifier. The dataset is now statistically diverse enough to target the 95% accuracy benchmark.