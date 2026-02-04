Workflow that streamlined git with notebook lm.

## **Documentation Sync Pipeline**

This system automates the synchronization of project documentation from **GitHub** to **NotebookLM** via the **Google Docs API**.

### **System Architecture**

- **Source of Truth:** Obsidian markdown files stored in the `/docs` directory of the GitHub repository.
    
- **Automation Engine:** GitHub Actions (Ubuntu runner) triggered on every `push` to the `main` branch.
    
- **Transport Layer:** A Python script utilizing the `google-api-python-client` and a Google Service Account.
    
- **Destination:** A persistent Google Doc acting as a "Live Source" for NotebookLM.
    

### **Pipeline Steps**

1. **Aggregation:** The GitHub Action scans the `/docs` folder and compiles all `.md` files into a single `master_knowledge.md` file, inserting source headers for each document.
    
2. **Authentication:** The script decodes a **Base64-encoded Service Account Key** (stored in GitHub Secrets) to authorize with Google Cloud.
    
3. **Content Management:** Instead of uploading a new file (which hits storage quotas), the script performs a **Batch Update**:
    
    - It calculates the length of the existing Google Doc.
        
    - It deletes all old content.
        
    - It inserts the newly aggregated text.
        
4. **AI Integration:** NotebookLM remains linked to the persistent Google Doc ID. When the Doc updates, the AI can be "refreshed" to ingest the latest project knowledge.
    

### **Technical Bypasses Implemented**

- **Quota Circumvention:** Used the **Google Docs API** to edit text within a user-owned document, bypassing the **0GB storage limit** assigned to free Google Service Accounts.
    
- **Persistence:** By targeting a specific **Document ID** rather than creating new files, the NotebookLM source link remains stable and never needs re-linking.