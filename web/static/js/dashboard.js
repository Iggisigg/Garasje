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

        // Update display values
        document.getElementById('mode').textContent = settings.mock_mode ? 'Mock' : 'Ekte';

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
        updateTeslaCard(data.tesla);
    }

    // Update recommendation
    if (data.recommendation) {
        updateRecommendation(data.recommendation);
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
function updateTeslaCard(tesla) {
    // Battery percentage
    document.getElementById('tesla-battery').textContent = `${tesla.battery_percent}%`;

    // Range
    document.getElementById('tesla-range').textContent = `${Math.round(tesla.range_km)} km`;

    // Battery bar
    const batteryBar = document.getElementById('tesla-battery-bar');
    batteryBar.style.width = `${tesla.battery_percent}%`;

    // Update battery bar color based on percentage
    if (tesla.battery_percent >= 80) {
        batteryBar.className = 'bg-green-500 h-3 rounded-full transition-all duration-500';
    } else if (tesla.battery_percent >= 50) {
        batteryBar.className = 'bg-yellow-500 h-3 rounded-full transition-all duration-500';
    } else if (tesla.battery_percent >= 20) {
        batteryBar.className = 'bg-orange-500 h-3 rounded-full transition-all duration-500';
    } else {
        batteryBar.className = 'bg-red-500 h-3 rounded-full transition-all duration-500';
    }

    // Location
    const locationText = tesla.location === 'home' ? 'Hjemme' : 'Borte';
    document.getElementById('tesla-location').textContent = locationText;

    // Charging status
    const chargingText = tesla.is_charging
        ? `Lader${tesla.charging_rate_kw ? ` (${tesla.charging_rate_kw} kW)` : ''}`
        : 'Lader ikke';
    document.getElementById('tesla-charging').textContent = chargingText;

    // Mock badge
    const mockBadge = document.getElementById('mock-badge');
    if (tesla.is_mock) {
        mockBadge.classList.remove('hidden');
    } else {
        mockBadge.classList.add('hidden');
    }
}

/**
 * Update recommendation card
 */
function updateRecommendation(recommendation) {
    const card = document.getElementById('recommendation-card');
    const action = document.getElementById('recommendation-action');
    const reason = document.getElementById('recommendation-reason');

    // Update text
    const actionMap = {
        'CHARGE': 'LAD',
        'NO_CHARGE': 'IKKE LAD',
        'CONTINUE_CHARGING': 'FORTSETT Å LADE'
    };

    action.textContent = actionMap[recommendation.action] || recommendation.action;
    reason.textContent = recommendation.reason;

    // Update card styling based on action
    card.className = 'rounded-lg shadow-md p-6 mb-6';

    if (recommendation.action === 'CHARGE') {
        card.classList.add('bg-blue-50', 'border', 'border-blue-200');
        action.className = 'text-lg font-medium mb-2 text-blue-700';
    } else if (recommendation.action === 'NO_CHARGE') {
        card.classList.add('bg-green-50', 'border', 'border-green-200');
        action.className = 'text-lg font-medium mb-2 text-green-700';
    } else {
        card.classList.add('bg-yellow-50', 'border', 'border-yellow-200');
        action.className = 'text-lg font-medium mb-2 text-yellow-700';
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
