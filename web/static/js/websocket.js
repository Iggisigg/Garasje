/**
 * WebSocket client for real-time updates
 */

class DashboardWebSocket {
    constructor() {
        this.ws = null;
        this.reconnectInterval = 3000; // 3 seconds
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.pingInterval = null;
        this.isIntentionallyClosed = false;

        this.connect();
    }

    connect() {
        // Determine WebSocket URL based on current page
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        console.log(`Connecting to WebSocket: ${wsUrl}`);

        try {
            this.ws = new WebSocket(wsUrl);
            this.setupEventHandlers();
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.scheduleReconnect();
        }
    }

    setupEventHandlers() {
        this.ws.onopen = () => {
            console.log('✓ WebSocket connected');
            this.reconnectAttempts = 0;
            this.updateConnectionStatus(true);

            // Start ping interval to keep connection alive
            this.startPingInterval();
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = () => {
            console.log('✗ WebSocket disconnected');
            this.updateConnectionStatus(false);
            this.stopPingInterval();

            if (!this.isIntentionallyClosed) {
                this.scheduleReconnect();
            }
        };
    }

    handleMessage(data) {
        console.log('WebSocket message received:', data.type);

        switch (data.type) {
            case 'initial_status':
            case 'status_update':
                // Dispatch custom event for dashboard to handle
                window.dispatchEvent(new CustomEvent('vehicle-status-update', {
                    detail: data
                }));
                break;

            case 'pong':
                // Ping response received
                break;

            default:
                console.warn('Unknown message type:', data.type);
        }
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket not connected. Cannot send message:', message);
        }
    }

    startPingInterval() {
        // Send ping every 30 seconds to keep connection alive
        this.pingInterval = setInterval(() => {
            this.send({ type: 'ping' });
        }, 30000);
    }

    stopPingInterval() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnect attempts reached. Giving up.');
            this.updateConnectionStatus(false, 'Mislyktes å koble til');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectInterval * Math.min(this.reconnectAttempts, 5);

        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

        setTimeout(() => {
            this.connect();
        }, delay);
    }

    updateConnectionStatus(connected, message = null) {
        const indicator = document.getElementById('ws-indicator');
        const text = document.getElementById('ws-text');

        if (connected) {
            indicator.className = 'w-3 h-3 rounded-full bg-green-500';
            text.textContent = 'Tilkoblet';
            text.className = 'text-green-600';
        } else {
            indicator.className = 'w-3 h-3 rounded-full bg-red-500';
            text.textContent = message || 'Frakoblet';
            text.className = 'text-red-600';
        }
    }

    requestStatus() {
        this.send({ type: 'request_status' });
    }

    close() {
        this.isIntentionallyClosed = true;
        this.stopPingInterval();
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Initialize WebSocket when page loads
let dashboardWS = null;

document.addEventListener('DOMContentLoaded', () => {
    dashboardWS = new DashboardWebSocket();
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (dashboardWS) {
        dashboardWS.close();
    }
});
