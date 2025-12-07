# Frontend - VERDICT Dashboard

This directory contains the web-based user interface for VERDICT.

## Structure

```
frontend/
├── dashboard.html       # Main trading analysis dashboard
└── verification.html    # Flare verification UI
```

## Files

### dashboard.html
The main dashboard interface for interacting with the VERDICT API. Features:
- Token analysis input form
- Real-time trading recommendations (LONG/SHORT/HOLD)
- Market data visualization
- Sentiment analysis results
- Component health monitoring
- Attack simulation controls
- Verification rules engine display

### verification.html
Specialized interface for Flare Network verification features:
- Flare Data Connector (FDC) integration
- FTSO price feed display
- Smart contract verification status
- Data attestation proof visualization

## Usage

### Development

1. **Start the backend server first:**
   ```bash
   cd ../backend
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Serve the frontend:**
   - **Option 1 - Simple HTTP Server:**
     ```bash
     python -m http.server 8080
     ```
   
   - **Option 2 - Direct file access:**
     Open `dashboard.html` directly in your browser
     
   - **Option 3 - VS Code Live Server:**
     Use the Live Server extension in VS Code

3. **Access the dashboard:**
   - Main Dashboard: `http://localhost:8080/dashboard.html`
   - Verification UI: `http://localhost:8080/verification.html`

### Configuration

The frontend connects to the backend API at `http://localhost:8000` by default. To change this:

1. Open the HTML file in a text editor
2. Find the API endpoint configuration (typically near the top of the `<script>` section)
3. Update the `API_URL` or similar constant to point to your backend server

Example:
```javascript
const API_URL = 'http://your-backend-url:8000';
```

## Features

- **Real-time Analysis**: Submit token analysis requests and view results
- **Dynamic Status Updates**: Auto-updating trading recommendations
- **Component Monitoring**: View health status of all backend components
- **Attack Simulation**: Test system resilience with simulated attacks
- **Flare Integration**: View blockchain verification data
- **Responsive Design**: Works on desktop and mobile devices

## API Integration

The frontend communicates with these backend endpoints:
- `POST /api/analyze` - Submit analysis requests
- `GET /api/component-status` - Fetch component health
- `POST /api/simulate-attack` - Trigger attack simulations
- `POST /api/reset-simulation` - Reset attack simulation
- `GET /api/rules` - Fetch verification rules

For complete API documentation, see `../CURL_COMMANDS.md`

## Troubleshooting

**CORS Errors:**
- Ensure the backend is running with proper CORS configuration
- Check that the API URL in the HTML matches your backend server

**Connection Refused:**
- Verify the backend server is running on the expected port
- Check firewall settings if accessing from a different machine

**No Data Displayed:**
- Open browser developer console (F12) to check for errors
- Verify API responses in the Network tab
- Ensure environment variables are properly configured in backend
