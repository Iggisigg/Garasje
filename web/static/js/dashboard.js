/**
 * Dashboard UI logic
 */

// State
let currentData = null;

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard initializing...');

    // Load initial data
    loadDashboard();

    // Load settings
    loadSettings();

    // Setup event listeners
    setupEventListeners();

    // Listen for WebSocket updates
    window.addEventListener('vehicle-status-update', (event) => {
        console.log('Received status update via WebSocket');
        updateUI(event.detail);
    });
});

/**
 * Load initial dashboard data
 */
async function loadDashboard() {
    try {
        const response = await fetch('/api/status');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        updateUI(data);

    } catch (error) {
        console.error('Failed to load dashboard:', error);
        showError('Kunne ikke laste data. Prøv å oppdatere siden.');
    }
}

/**
 * Load settings from API
 */
async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        if (!response.ok) return;

        const settings = await response.json();

        // Update threshold slider
        const slider = document.getElementById('threshold-slider');
        slider.value = settings.charge_threshold;
        document.getElementById('threshold-value').textContent = settings.charge_threshold;

        // Update mock mode checkboxes
        document.getElementById('tesla-mock-checkbox').checked = settings.tesla_mock_mode;
        document.getElementById('ioniq-mock-checkbox').checked = settings.ioniq_mock_mode;

        // Update display values
        document.getElementById('tesla-mode').textContent = settings.tesla_mock_mode ? 'Mock' : 'Ekte';
        document.getElementById('ioniq-mode').textContent = settings.ioniq_mock_mode ? 'Mock' : 'Ekte';

    } catch (error) {
        console.error('Failed to load settings:', error);
    }
}

/**
 * Update UI with new data
 */
function updateUI(data) {
    currentData = data;

    // Update Tesla data
    if (data.tesla) {
        updateTeslaCard(data.tesla, data.tesla_recommendation);
    }

    // Update Ioniq data
    if (data.ioniq) {
        updateIoniqCard(data.ioniq, data.ioniq_recommendation);
        document.getElementById('ioniq-card').classList.remove('hidden');
    } else {
        document.getElementById('ioniq-card').classList.add('hidden');
    }

    // Update priority vehicle
    if (data.priority_vehicle) {
        updatePriorityVehicle(data.priority_vehicle);
    }

    // Update timestamps
    if (data.last_updated) {
        const time = new Date(data.last_updated).toLocaleTimeString('no-NO', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        document.getElementById('last-updated').textContent = time;
    }

    if (data.next_update) {
        const time = new Date(data.next_update).toLocaleTimeString('no-NO', {
            hour: '2-digit',
            minute: '2-digit'
        });
        document.getElementById('next-update').textContent = time;
    }
}

/**
 * Update Tesla card
 */
function updateTeslaCard(tesla, recommendation) {
    // Battery percentage
    document.getElementById('tesla-battery').textContent = `${tesla.battery_percent}%`;

    // Range
    document.getElementById('tesla-range').textContent = `${Math.round(tesla.range_km)} km`;

    // Battery bar
    const batteryBar = document.getElementById('tesla-battery-bar');
    batteryBar.style.width = `${tesla.battery_percent}%`;

    // Update battery bar color based on percentage
    if (tesla.battery_percent >= 80) {
        batteryBar.className = 'bg-green-500 h-2 rounded-full transition-all duration-500';
    } else if (tesla.battery_percent >= 50) {
        batteryBar.className = 'bg-yellow-500 h-2 rounded-full transition-all duration-500';
    } else if (tesla.battery_percent >= 20) {
        batteryBar.className = 'bg-orange-500 h-2 rounded-full transition-all duration-500';
    } else {
        batteryBar.className = 'bg-red-500 h-2 rounded-full transition-all duration-500';
    }

    // Location - show address instead of "Hjemme/Borte"
    let locationText = 'Ukjent posisjon';
    if (tesla.address) {
        locationText = tesla.address;
    } else if (tesla.latitude && tesla.longitude) {
        locationText = `${tesla.latitude.toFixed(4)}°, ${tesla.longitude.toFixed(4)}°`;
    }
    document.getElementById('tesla-location').textContent = locationText;

    // Charging status
    const chargingText = tesla.is_charging
        ? `Lader${tesla.charging_rate_kw ? ` (${tesla.charging_rate_kw} kW)` : ''}`
        : 'Lader ikke';
    document.getElementById('tesla-charging').textContent = chargingText;

    // Recommendation
    if (recommendation) {
        const actionMap = {
            'CHARGE': 'LAD',
            'NO_CHARGE': 'IKKE LAD',
            'CONTINUE_CHARGING': 'FORTSETT'
        };
        document.getElementById('tesla-recommendation').textContent =
            actionMap[recommendation.action] || recommendation.action;
    }

    // Mock badge
    const mockBadge = document.getElementById('tesla-mock-badge');
    if (tesla.is_mock) {
        mockBadge.classList.remove('hidden');
    } else {
        mockBadge.classList.add('hidden');
    }
}

/**
 * Update Ioniq card
 */
function updateIoniqCard(ioniq, recommendation) {
    // Battery percentage
    document.getElementById('ioniq-battery').textContent = `${ioniq.battery_percent}%`;

    // Range
    document.getElementById('ioniq-range').textContent = `${Math.round(ioniq.range_km)} km`;

    // Battery bar
    const batteryBar = document.getElementById('ioniq-battery-bar');
    batteryBar.style.width = `${ioniq.battery_percent}%`;

    // Update battery bar color based on percentage
    if (ioniq.battery_percent >= 80) {
        batteryBar.className = 'bg-purple-500 h-2 rounded-full transition-all duration-500';
    } else if (ioniq.battery_percent >= 50) {
        batteryBar.className = 'bg-yellow-500 h-2 rounded-full transition-all duration-500';
    } else if (ioniq.battery_percent >= 20) {
        batteryBar.className = 'bg-orange-500 h-2 rounded-full transition-all duration-500';
    } else {
        batteryBar.className = 'bg-red-500 h-2 rounded-full transition-all duration-500';
    }

    // Location
    const locationText = ioniq.location === 'home' ? 'Hjemme' : 'Borte';
    document.getElementById('ioniq-location').textContent = locationText;

    // Charging status
    const chargingText = ioniq.is_charging
        ? `Lader${ioniq.charging_rate_kw ? ` (${ioniq.charging_rate_kw} kW)` : ''}`
        : 'Lader ikke';
    document.getElementById('ioniq-charging').textContent = chargingText;

    // Recommendation
    if (recommendation) {
        const actionMap = {
            'CHARGE': 'LAD',
            'NO_CHARGE': 'IKKE LAD',
            'CONTINUE_CHARGING': 'FORTSETT'
        };
        document.getElementById('ioniq-recommendation').textContent =
            actionMap[recommendation.action] || recommendation.action;
    }

    // Mock badge
    const mockBadge = document.getElementById('ioniq-mock-badge');
    if (ioniq.is_mock) {
        mockBadge.classList.remove('hidden');
    } else {
        mockBadge.classList.add('hidden');
    }
}

/**
 * Update priority vehicle display
 */
function updatePriorityVehicle(priorityVehicle) {
    const element = document.getElementById('priority-vehicle');
    const card = document.getElementById('recommendation-card');

    if (priorityVehicle === 'NONE') {
        element.textContent = 'Ingen bil trenger lading';
        card.className = 'rounded-lg shadow-md p-6 mb-6 bg-green-50 border border-green-200';
    } else {
        element.textContent = priorityVehicle;
        card.className = 'rounded-lg shadow-md p-6 mb-6 bg-blue-50 border border-blue-200';
    }
}


/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Update button
    document.getElementById('btn-update').addEventListener('click', async () => {
        await triggerManualUpdate();
    });

    // History button
    document.getElementById('btn-history').addEventListener('click', () => {
        showHistory();
    });

    // Settings toggle
    const settingsToggle = document.getElementById('settings-toggle');
    const settingsContent = document.getElementById('settings-content');
    const settingsChevron = document.getElementById('settings-chevron');

    settingsToggle.addEventListener('click', () => {
        settingsContent.classList.toggle('hidden');
        settingsChevron.classList.toggle('rotate-180');
    });

    // Threshold slider
    const slider = document.getElementById('threshold-slider');
    const valueDisplay = document.getElementById('threshold-value');

    slider.addEventListener('input', (e) => {
        valueDisplay.textContent = e.target.value;
    });

    slider.addEventListener('change', async (e) => {
        await updateThreshold(parseInt(e.target.value));
    });

    // Mock mode checkboxes
    document.getElementById('tesla-mock-checkbox').addEventListener('change', async (e) => {
        await updateMockMode('tesla', e.target.checked);
    });

    document.getElementById('ioniq-mock-checkbox').addEventListener('change', async (e) => {
        await updateMockMode('ioniq', e.target.checked);
    });
}

/**
 * Trigger manual update
 */
async function triggerManualUpdate() {
    const button = document.getElementById('btn-update');
    const loadingOverlay = document.getElementById('loading-overlay');

    try {
        // Disable button and show loading
        button.disabled = true;
        button.classList.add('opacity-50', 'cursor-not-allowed');
        loadingOverlay.classList.remove('hidden');

        const response = await fetch('/api/update', {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        // Data will arrive via WebSocket, just wait a moment
        await new Promise(resolve => setTimeout(resolve, 1000));

    } catch (error) {
        console.error('Manual update failed:', error);
        showError('Oppdatering mislyktes. Prøv igjen.');
    } finally {
        // Re-enable button and hide loading
        button.disabled = false;
        button.classList.remove('opacity-50', 'cursor-not-allowed');
        loadingOverlay.classList.add('hidden');
    }
}

/**
 * Show history (simple alert for now)
 */
async function showHistory() {
    try {
        const response = await fetch('/api/history?hours=24');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        const count = data.readings.length;

        alert(`Historikk (siste 24 timer):\n\n${count} målinger lagret\n\n(Detaljert visning kommer i fremtidig versjon)`);

    } catch (error) {
        console.error('Failed to fetch history:', error);
        showError('Kunne ikke hente historikk.');
    }
}

/**
 * Update threshold setting
 */
async function updateThreshold(threshold) {
    try {
        const response = await fetch(`/api/settings/threshold?threshold=${threshold}`, {
            method: 'PUT'
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        console.log(`Threshold updated to ${threshold}%`);

        // Reload dashboard to reflect new threshold
        loadDashboard();

    } catch (error) {
        console.error('Failed to update threshold:', error);
        showError('Kunne ikke oppdatere terskel.');
    }
}

/**
 * Update mock mode for a vehicle
 */
async function updateMockMode(vehicle, enabled) {
    try {
        const response = await fetch(`/api/settings/mock-mode/${vehicle}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ enabled: enabled })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        console.log(`${vehicle} mock mode ${enabled ? 'enabled' : 'disabled'}`);

        // Reload settings and dashboard
        await loadSettings();
        await loadDashboard();

    } catch (error) {
        console.error(`Failed to update ${vehicle} mock mode:`, error);
        showError(`Kunne ikke oppdatere ${vehicle} mock mode.`);

        // Revert checkbox on error
        const checkbox = document.getElementById(`${vehicle}-mock-checkbox`);
        checkbox.checked = !enabled;
    }
}

/**
 * Show error message (simple alert for now)
 */
function showError(message) {
    alert(`⚠️ Feil: ${message}`);
}

/**
 * Format date/time for display
 */
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('no-NO', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}
