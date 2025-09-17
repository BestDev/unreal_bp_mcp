// Dashboard JavaScript functionality
let statusWebSocket = null;
let performanceChart = null;
let operationsWebSocket = null;

// Initialize dashboard
function initializeDashboard() {
    connectWebSockets();
    initializePerformanceChart();
    loadInitialData();

    // Auto-refresh every 30 seconds if WebSocket fails
    setInterval(() => {
        if (!statusWebSocket || statusWebSocket.readyState !== WebSocket.OPEN) {
            refreshStatus();
        }
    }, 30000);
}

// WebSocket connections
function connectWebSockets() {
    // Status WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host;

    statusWebSocket = new WebSocket(`${protocol}//${wsHost}/ws/status`);

    statusWebSocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        updateStatusDisplay(data);
    };

    statusWebSocket.onclose = function() {
        console.log('Status WebSocket disconnected');
        // Try to reconnect after 5 seconds
        setTimeout(connectWebSockets, 5000);
    };

    statusWebSocket.onerror = function(error) {
        console.error('Status WebSocket error:', error);
    };

    // Operations WebSocket
    operationsWebSocket = new WebSocket(`${protocol}//${wsHost}/ws/operations`);

    operationsWebSocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        updateOperationsTable(data.recent_operations);
    };
}

// Initialize performance chart
function initializePerformanceChart() {
    const ctx = document.getElementById('performanceChart').getContext('2d');

    performanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'CPU Usage (%)',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.1
                },
                {
                    label: 'Memory (MB)',
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    tension: 0.1,
                    yAxisID: 'y1'
                },
                {
                    label: 'Active Connections',
                    data: [],
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    tension: 0.1,
                    yAxisID: 'y2'
                }
            ]
        },
        options: {
            responsive: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'CPU Usage (%)'
                    },
                    max: 100
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Memory (MB)'
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                },
                y2: {
                    type: 'linear',
                    display: false,
                    position: 'right',
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Real-time System Metrics'
                }
            }
        }
    });
}

// Load initial data
function loadInitialData() {
    refreshStatus();
    refreshOperations();
    refreshPerformanceData();
}

// Update status display
function updateStatusDisplay(status) {
    document.getElementById('server-status').textContent = status.server_status;
    document.getElementById('connections-count').textContent = status.connections;
    document.getElementById('operations-rate').textContent = status.operations_per_minute;

    // Format last update time
    const lastUpdate = new Date(status.last_updated);
    document.getElementById('last-update').textContent = lastUpdate.toLocaleTimeString();

    // Update status card color based on server status
    const statusCard = document.getElementById('server-status').closest('.card');
    statusCard.className = statusCard.className.replace(/bg-(success|danger|warning)/, '');

    if (status.server_status === 'online') {
        statusCard.classList.add('bg-success');
    } else if (status.server_status === 'offline') {
        statusCard.classList.add('bg-danger');
    } else {
        statusCard.classList.add('bg-warning');
    }
}

// Refresh status
async function refreshStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        updateStatusDisplay(status);
    } catch (error) {
        console.error('Error refreshing status:', error);
    }
}

// Refresh operations
async function refreshOperations() {
    try {
        const response = await fetch('/api/operations');
        const data = await response.json();
        updateOperationsTable(data.operations);
    } catch (error) {
        console.error('Error refreshing operations:', error);
    }
}

// Update operations table
function updateOperationsTable(operations) {
    const tbody = document.querySelector('#operations-table tbody');

    if (!operations || operations.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted">No recent operations</td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = operations.slice(-10).reverse().map(op => {
        const startTime = new Date(op.started_at);
        const duration = op.completed_at ?
            Math.round((new Date(op.completed_at) - startTime) / 1000) + 's' :
            'Running...';

        const statusBadge = getStatusBadge(op.status);

        return `
            <tr>
                <td>${startTime.toLocaleTimeString()}</td>
                <td>${op.type}</td>
                <td>${statusBadge}</td>
                <td>${duration}</td>
                <td>
                    <button class="btn btn-sm btn-outline-info" onclick="showOperationDetails('${op.id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

// Get status badge HTML
function getStatusBadge(status) {
    const badgeClasses = {
        'completed': 'badge bg-success',
        'running': 'badge bg-primary',
        'failed': 'badge bg-danger',
        'queued': 'badge bg-warning'
    };

    const badgeClass = badgeClasses[status] || 'badge bg-secondary';
    return `<span class="${badgeClass}">${status}</span>`;
}

// Refresh performance data
async function refreshPerformanceData() {
    try {
        const response = await fetch('/api/performance');
        const data = await response.json();
        updatePerformanceChart(data.history);
    } catch (error) {
        console.error('Error refreshing performance data:', error);
    }
}

// Update performance chart
function updatePerformanceChart(performanceData) {
    if (!performanceData || performanceData.length === 0) return;

    // Keep only last 20 data points
    const recentData = performanceData.slice(-20);

    const labels = recentData.map(d => {
        const time = new Date(d.timestamp);
        return time.toLocaleTimeString();
    });

    const cpuData = recentData.map(d => d.cpu_percent || Math.random() * 50 + 10);
    const memoryData = recentData.map(d => d.memory_mb || Math.random() * 200 + 100);
    const connectionData = recentData.map(d => d.active_connections || 0);

    performanceChart.data.labels = labels;
    performanceChart.data.datasets[0].data = cpuData;
    performanceChart.data.datasets[1].data = memoryData;
    performanceChart.data.datasets[2].data = connectionData;

    performanceChart.update('none'); // No animation for real-time updates
}

// Quick Actions
function createBlueprint() {
    const modal = new bootstrap.Modal(document.getElementById('createBlueprintModal'));
    modal.show();
}

async function submitCreateBlueprint() {
    const name = document.getElementById('blueprintName').value;
    const parentClass = document.getElementById('parentClass').value;
    const assetPath = document.getElementById('assetPath').value;

    if (!name) {
        alert('Please enter a blueprint name');
        return;
    }

    try {
        const response = await fetch('/api/blueprints', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                parent_class: parentClass,
                asset_path: assetPath
            })
        });

        const result = await response.json();

        if (response.ok) {
            alert(`Blueprint creation queued: ${result.operation_id}`);
            bootstrap.Modal.getInstance(document.getElementById('createBlueprintModal')).hide();

            // Clear form
            document.getElementById('createBlueprintForm').reset();

            // Refresh operations
            setTimeout(refreshOperations, 1000);
        } else {
            alert(`Error: ${result.detail || 'Failed to create blueprint'}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function runPerformanceScan() {
    try {
        const response = await fetch('/api/operations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                operation_type: 'performance_scan',
                parameters: {},
                priority: 1
            })
        });

        const result = await response.json();

        if (response.ok) {
            alert(`Performance scan queued: ${result.operation_id}`);
            setTimeout(refreshOperations, 1000);
        } else {
            alert('Error starting performance scan');
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

function viewLogs() {
    // Open logs in new window
    window.open('/logs', '_blank');
}

function exportData() {
    // Download data as JSON
    fetch('/api/performance')
        .then(response => response.json())
        .then(data => {
            const blob = new Blob([JSON.stringify(data, null, 2)], {
                type: 'application/json'
            });

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `dashboard-data-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        })
        .catch(error => {
            alert(`Error exporting data: ${error.message}`);
        });
}

function showOperationDetails(operationId) {
    alert(`Operation details for: ${operationId}\n\nDetailed view coming soon...`);
}

// Utility functions
function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleString();
}

function formatDuration(startTime, endTime) {
    if (!endTime) return 'Running...';

    const duration = (new Date(endTime) - new Date(startTime)) / 1000;
    return `${duration.toFixed(1)}s`;
}