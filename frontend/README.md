# **VectorShift Integration Assessment Documentation**

## **Overview**
This project integrates third-party services (HubSpot, Airtable, and Notion) using FastAPI for the backend and React with MUI for the frontend. It supports OAuth flows, data retrieval, and displays the retrieved data in a structured format. The system uses Redis for caching credentials and Celery for background tasks.

---

## **1. Backend**

### **Main Functionalities**
- **OAuth Flow:** Each integration handles OAuth 2.0 authorization, using a `/authorize` endpoint to initiate and an `/oauth2callback` to handle the callback.
- **Credential Retrieval:** Credentials are fetched from Redis using the `/credentials` endpoint.
- **Data Loading:** Data from each integration is retrieved using `/load` endpoints.

### **Testing**
- Tests use `pytest` and are located in the `tests/` directory.
- `conftest.py` contains test fixtures for Redis mocks.
- Individual test files (`test_hubspot.py`, `test_airtable.py`, `test_notion.py`) cover:
  - Authorization requests
  - Credential retrieval
  - Data loading

#### **How to Run Backend Tests**
```bash
# Navigate to the backend directory
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_hubspot.py
```

---

## **2. Frontend**

### **Main Functionalities**
- **Integration Form:** Handles user input for user ID, organization ID, and integration selection.
- **OAuth Connection:** Each integration component handles its OAuth flow and updates `integrationParams`.
- **Data Display:** `DataForm` component displays the retrieved data in a text field with JSON formatting.

### **Testing**
- Uses `Jest` and `React Testing Library`.
- Mocks Axios for API requests.
- Test files are located in the `src/` directory, following the component structure.

#### **How to Run Frontend Tests**
```bash
# Navigate to the frontend directory
cd frontend

# Run all tests
npm test

# Run specific test file
npm test src/integrations/hubspot.test.js
```

---

## **3. Environment Variables**
Configure environment variables in a `.env` file for backend.

---

## **4. Running the Project**

```bash
# Start Redis server
redis-server

# Navigate to the /frontend directory
npm i
npm start

# Navigate to the /backend directory
uvicorn main:app —reload
```

---

## **5. API Endpoints Reference**

### **HubSpot Integration**
- `POST /integrations/hubspot/authorize` - Initiates OAuth flow
- `POST /integrations/hubspot/credentials` - Retrieves stored credentials
- `POST /integrations/hubspot/load` - Loads data from HubSpot

### **Airtable Integration**
- `POST /integrations/airtable/authorize` - Initiates OAuth flow
- `POST /integrations/airtable/credentials` - Retrieves stored credentials
- `POST /integrations/airtable/load` - Loads data from Airtable

### **Notion Integration**
- `POST /integrations/notion/authorize` - Initiates OAuth flow
- `POST /integrations/notion/credentials` - Retrieves stored credentials
- `POST /integrations/notion/load` - Loads data from Notion

---

