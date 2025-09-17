# Web Dashboard for UnrealBlueprintMCP

A real-time web interface for monitoring and controlling MCP operations, providing comprehensive project management and performance insights.

## 🌐 Features Overview

### 📊 Real-time Monitoring
**File**: `dashboard_server.py`
- Live performance metrics and system status
- WebSocket connection monitoring
- Tool execution time tracking
- Error rate and success statistics

### 🎛️ Blueprint Management
**File**: `blueprint_manager.py`
- Visual blueprint browser and editor
- Bulk operations interface
- Property editing and validation
- Asset organization tools

### 📈 Performance Analytics
**File**: `performance_analytics.py`
- Historical performance data visualization
- Trend analysis and predictions
- Resource usage optimization suggestions
- Benchmarking and comparison tools

### 🔧 Remote Control Interface
**File**: `remote_controller.py`
- Execute MCP operations from web interface
- Batch operation queue management
- Real-time operation status tracking
- Error handling and retry mechanisms

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Dashboard**
   ```bash
   python dashboard_server.py
   ```

3. **Access Web Interface**
   ```
   http://localhost:8080
   ```

## 📁 Directory Structure

```
web_dashboard/
├── dashboard_server.py      # Main FastAPI server
├── blueprint_manager.py     # Blueprint management backend
├── performance_analytics.py # Analytics and reporting
├── remote_controller.py     # Remote operation controls
├── static/                  # Static web assets
│   ├── css/
│   ├── js/
│   └── images/
├── templates/               # HTML templates
│   ├── index.html
│   ├── blueprints.html
│   ├── performance.html
│   └── settings.html
└── requirements.txt
```

## 🎨 User Interface

### Dashboard Home
- System status overview
- Active connections display
- Recent operations log
- Quick action buttons

### Blueprint Browser
- Hierarchical project view
- Blueprint property inspector
- Batch operation tools
- Search and filtering

### Performance Monitor
- Real-time metrics charts
- Historical data analysis
- System resource monitoring
- Performance optimization tips

### Settings Panel
- Server configuration
- Connection management
- User preferences
- Export/import options

## 🔧 API Endpoints

### REST API
```
GET    /api/status           # System status
GET    /api/blueprints       # List blueprints
POST   /api/blueprints       # Create blueprint
PUT    /api/blueprints/{id}  # Update blueprint
DELETE /api/blueprints/{id}  # Delete blueprint
GET    /api/performance      # Performance metrics
GET    /api/operations       # Operation history
POST   /api/operations       # Queue operation
```

### WebSocket API
```
/ws/status        # Real-time status updates
/ws/operations    # Operation progress updates
/ws/performance   # Live performance metrics
/ws/logs          # Real-time log streaming
```

## 📊 Monitoring Features

### System Metrics
- CPU and memory usage
- Network traffic monitoring
- Disk space utilization
- Process health status

### MCP Server Metrics
- Connection count and status
- Tool execution statistics
- Error rates and types
- Response time analysis

### Unreal Engine Integration
- Plugin status monitoring
- Blueprint compilation status
- Asset modification tracking
- Editor performance metrics

## 🔒 Security Features

### Authentication
- Optional user authentication
- API key management
- Session management
- Role-based access control

### Data Protection
- HTTPS support
- Data encryption
- Audit logging
- Input validation

## 🎯 Usage Examples

### Monitoring Dashboard
```python
# Access real-time metrics
import requests

response = requests.get("http://localhost:8080/api/status")
status = response.json()

print(f"Server Status: {status['server_status']}")
print(f"Active Connections: {status['connections']}")
print(f"Operations/minute: {status['operations_per_minute']}")
```

### Remote Blueprint Creation
```javascript
// JavaScript example for web interface
async function createBlueprint(name, parentClass) {
    const response = await fetch('/api/blueprints', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            name: name,
            parent_class: parentClass,
            asset_path: '/Game/Blueprints/'
        })
    });

    return await response.json();
}
```

### Real-time Updates
```javascript
// WebSocket connection for live updates
const ws = new WebSocket('ws://localhost:8080/ws/status');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    updateDashboard(data);
};
```

## 🔧 Configuration

### Server Configuration
```python
# config.py
DASHBOARD_CONFIG = {
    "host": "localhost",
    "port": 8080,
    "debug": False,
    "auto_reload": True,
    "cors_origins": ["*"],
    "websocket_timeout": 300
}
```

### Database Configuration
```python
# Optional database for persistent storage
DATABASE_CONFIG = {
    "url": "sqlite:///dashboard.db",
    "echo": False,
    "pool_size": 10,
    "max_overflow": 20
}
```

## 📱 Responsive Design

The dashboard is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile devices
- Various screen resolutions

## 🎨 Customization

### Themes
- Light and dark mode support
- Customizable color schemes
- Branded styling options
- High contrast accessibility mode

### Layout
- Configurable widget placement
- Resizable panels
- Collapsible sections
- Custom dashboard layouts

## 🔍 Troubleshooting

### Common Issues
1. **Port already in use**: Change port in configuration
2. **WebSocket connection fails**: Check firewall settings
3. **Slow performance**: Reduce update frequency
4. **Memory usage**: Enable data cleanup options

### Debug Mode
```bash
python dashboard_server.py --debug --verbose
```

## 📈 Performance Optimization

### Client-side
- Efficient DOM updates
- Data virtualization for large lists
- Progressive loading
- Caching strategies

### Server-side
- Async request handling
- Connection pooling
- Data aggregation
- Response compression

## 🔗 Integration

### CI/CD Integration
- Build status monitoring
- Deployment tracking
- Test result display
- Performance regression detection

### External Tools
- Slack notifications
- Email alerts
- Webhook integrations
- API monitoring tools

## 📚 Dependencies

- **FastAPI**: Modern web framework
- **Jinja2**: Template engine
- **SQLAlchemy**: Database ORM (optional)
- **Plotly**: Interactive charts
- **Bootstrap**: UI framework
- **jQuery**: JavaScript utilities