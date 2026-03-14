async function syncData() {
    const btn = document.getElementById('syncBtn');
    btn.disabled = true;
    btn.innerText = 'Syncing...';
    try {
        const response = await fetch('/sync', { method: 'POST' });
        if (response.ok) {
            location.reload();
        } else {
            alert('Sync failed!');
            btn.disabled = false;
            btn.innerText = 'Sync Now';
        }
    } catch (e) {
        console.error(e);
        btn.disabled = false;
        btn.innerText = 'Sync Now';
    }
}

function filterPolls(pollType) {
    const url = new URL(window.location);
    if (pollType) {
        url.searchParams.set('poll_type', pollType);
    } else {
        url.searchParams.delete('poll_type');
    }
    window.location.href = url.toString();
}

function initCharts(historyData) {
    Object.entries(historyData).forEach(([type, data]) => {
        const chartId = `chart-${type.replace(/ /g, '-').replace(/\./g, '')}`;
        const ctx = document.getElementById(chartId).getContext('2d');
        
        let posLabel = 'Pos';
        let negLabel = 'Neg';
        
        if (type === 'Generic Congressional Vote') {
            posLabel = 'Democrat';
            negLabel = 'Republican';
        } else if (type === 'Pres. Approval') {
            posLabel = 'Approve';
            negLabel = 'Disapprove';
        }

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.date_label),
                datasets: [
                    {
                        label: posLabel,
                        data: data.map(d => d.positive_avg),
                        borderColor: '#2845a7',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.3
                    },
                    {
                        label: negLabel,
                        data: data.map(d => d.negative_avg),
                        borderColor: '#dc3545',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: true }
                },
                scales: {
                    x: { 
                        display: true,
                        ticks: {
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 4,
                            font: { size: 10 }
                        },
                        grid: { display: false }
                    },
                    y: { 
                        display: true,
                        ticks: {
                            font: { size: 10 },
                            callback: function(value) { return value + '%'; }
                        },
                        grid: { color: '#eee' }
                    }
                }
            }
        });
    });
}
