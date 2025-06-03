// Update dashboard statistics
function updateDashboardStats() {
    fetch('/api/statistics')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('total-vehicles').textContent = data.statistics.total_vehicles;
                document.getElementById('current-vehicles').textContent = data.statistics.current_vehicles;
                document.getElementById('total-revenue').textContent = `${data.statistics.total_revenue} RWF`;
                document.getElementById('unauthorized-exits').textContent = data.statistics.unauthorized_exits;
            }
        })
        .catch(error => console.error('Error fetching statistics:', error));
}

// Update vehicles table
function updateVehiclesTable() {
    fetch('/api/vehicles')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tableBody = document.getElementById('vehicles-table');
                tableBody.innerHTML = '';
                
                data.vehicles.forEach(vehicle => {
                    const row = document.createElement('tr');
                    
                    const status = vehicle.payment_status === 1 ? 
                        '<span class="status-badge status-paid">Paid</span>' : 
                        '<span class="status-badge status-unpaid">Unpaid</span>';
                    
                    row.innerHTML = `
                        <td>${vehicle.plate_number}</td>
                        <td>${new Date(vehicle.entry_time).toLocaleString()}</td>
                        <td>${status}</td>
                        <td>${vehicle.payment_amount || '-'} RWF</td>
                    `;
                    
                    tableBody.appendChild(row);
                });
            }
        })
        .catch(error => console.error('Error fetching vehicles:', error));
}

// Update unauthorized exits table
function updateUnauthorizedExits() {
    fetch('/api/unauthorized_exits')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tableBody = document.getElementById('unauthorized-exits-table');
                tableBody.innerHTML = '';
                
                data.exits.forEach(exit => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${exit.plate_number}</td>
                        <td>${new Date(exit.exit_time).toLocaleString()}</td>
                    `;
                    tableBody.appendChild(row);
                });
            }
        })
        .catch(error => console.error('Error fetching unauthorized exits:', error));
}

// Initialize WebSocket connection for real-time updates
function initializeWebSocket() {
    const ws = new WebSocket(`ws://${window.location.host}/ws`);
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.type === 'vehicle_update') {
            updateVehiclesTable();
            updateDashboardStats();
        } else if (data.type === 'unauthorized_exit') {
            updateUnauthorizedExits();
            updateDashboardStats();
        }
    };
    
    ws.onclose = function() {
        // Try to reconnect after 5 seconds
        setTimeout(initializeWebSocket, 5000);
    };
}

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Initial updates
    updateDashboardStats();
    updateVehiclesTable();
    updateUnauthorizedExits();
    
    // Set up periodic updates
    setInterval(updateDashboardStats, 5000);
    setInterval(updateVehiclesTable, 10000);
    setInterval(updateUnauthorizedExits, 10000);
    
    // Initialize WebSocket
    initializeWebSocket();
}); 