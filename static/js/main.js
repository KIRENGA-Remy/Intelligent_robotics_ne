// Update statistics every 5 seconds
function updateStatistics() {
    fetch('/api/statistics')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('current-vehicles').textContent = data.statistics.current_vehicles;
                document.getElementById('total-revenue').textContent = `${data.statistics.total_revenue} RWF`;
            }
        })
        .catch(error => console.error('Error fetching statistics:', error));
}

// Update activity feed
function updateActivityFeed() {
    fetch('/api/vehicles')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const activityFeed = document.getElementById('activity-feed');
                activityFeed.innerHTML = '';
                
                // Get the 5 most recent vehicles
                const recentVehicles = data.vehicles.slice(0, 5);
                
                recentVehicles.forEach(vehicle => {
                    const activityItem = document.createElement('div');
                    activityItem.className = 'activity-item';
                    
                    const status = vehicle.payment_status === 1 ? 
                        '<span class="status-badge status-paid">Paid</span>' : 
                        '<span class="status-badge status-unpaid">Unpaid</span>';
                    
                    activityItem.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${vehicle.plate_number}</strong>
                                <small class="text-muted d-block">Entry: ${new Date(vehicle.entry_time).toLocaleString()}</small>
                            </div>
                            ${status}
                        </div>
                    `;
                    
                    activityFeed.appendChild(activityItem);
                });
            }
        })
        .catch(error => console.error('Error fetching vehicles:', error));
}

// Initialize WebSocket connection for real-time updates
function initializeWebSocket() {
    const ws = new WebSocket(`ws://${window.location.host}/ws`);
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.type === 'plate_detected') {
            document.getElementById('detected-plate').textContent = data.plate_number;
            updateActivityFeed();
        }
    };
    
    ws.onclose = function() {
        // Try to reconnect after 5 seconds
        setTimeout(initializeWebSocket, 5000);
    };
}

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    // Initial updates
    updateStatistics();
    updateActivityFeed();
    
    // Set up periodic updates
    setInterval(updateStatistics, 5000);
    setInterval(updateActivityFeed, 10000);
    
    // Initialize WebSocket
    initializeWebSocket();
}); 