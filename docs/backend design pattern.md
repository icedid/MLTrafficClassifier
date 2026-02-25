
## **Technical Design Document: Network Engine Strategy**

### **1. Architectural Overview**

The system utilizes the **Strategy Pattern** to decouple the data acquisition and classification logic from the presentation layer (FastAPI/HTMX). This ensures that the high-level module (the Web Router) does not depend on low-level modules (specific ML models or Scrapers), but rather on a common **Abstraction**.

### **2. Component Breakdown**

#### **A. The Abstraction (Strategy Interface)**

- **Location:** `backend.core.base.NetworkEngineProvider`
    
- **Technical Role:** An **Abstract Base Class (ABC)** that defines the interface requirements.
    
- **Constraint Enforcement:** It uses the `@abstractmethod` decorator to ensure that any concrete implementation provides the necessary hook methods. This prevents `AttributeError` at runtime by failing at instantiation if the contract is incomplete.
    

#### **B. The Concrete Strategies (Implementations)**

- **Technical Role:** These classes (e.g., `MLEngine`, `ScraperEngine`) encapsulate specific algorithms.
    
- **Polymorphism:** Because they inherit from the Base Class, they are **polymorphic**. The FastAPI application can treat an instance of `MLEngine` exactly the same as `ScraperEngine` because they share the same method signatures.
    

#### **C. The Context (Client)**

- **Location:** `frontend.router`
    
- **Technical Role:** The Context maintains a reference to a `NetworkEngineProvider` object. It does not instantiate the strategy itself but is "injected" with one (Dependency Injection).
    
- **Execution Flow:** 1. The Router receives an HTTP GET request from HTMX.
    
    2. The Router calls `active_provider.get_formatted_update()`.
    
    3. The specific Strategy executes its internal logic and returns a standardized `dict`.
    

---

### **3. Dependency Inversion Principle (DIP)**

Traditionally, a web app might import a specific model directly. In this pattern, we invert that:

- **Traditional:** `Router` $\to$ `ML_Model` (High-level depends on Low-level)
    
- **Our Pattern:** `Router` $\to$ `Interface` $\leftarrow$ `ML_Model` (Both depend on an Abstraction)
    

### **4. Data Flow Sequence**

1. **Trigger:** Client-side HTMX issues an asynchronous XHR request every $n$ seconds.
    
2. **Dispatch:** FastAPI identifies the route and accesses the `app.state.provider` (The Strategy Context).
    
3. **Encapsulation:** The Provider executes `capture_data()` $\to$ `process()` internally.
    
4. **Serialization:** The Provider returns a Python `Dictionary`.
    
5. **Rendering:** Jinja2 injects the dictionary values into a partial HTML template.
    
6. **Swap:** HTMX performs an out-of-band (OOB) or inner-HTML swap to update the DOM.
    

---

### **5. Technical Benefits for the Project**

- **Hot-Swapping:** The engine can be swapped in `main.py` without modifying the `frontendrouter.py` logic.
    
- **Concurrency:** The engine can run in a separate thread or process (using `asyncio` or `multiprocessing`) while the frontend remains responsive.
    
- **Mocking:** Facilitates **Unit Testing** by allowing a `MockProvider` to simulate network edge cases (e.g., 0% confidence, empty packets) without requiring a live network interface.
    
