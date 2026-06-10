document.addEventListener('DOMContentLoaded', () => {
    const chatWindow = document.getElementById('chat-window');
    const memoryBody = document.getElementById('memory-body');
    const timelineContainer = document.getElementById('timeline-container');
    const valLatency = document.getElementById('val-latency');
    const valCost = document.getElementById('val-cost');
    
    // App Controls
    const btnRunAuditor = document.getElementById('btn-run-auditor');
    const btnResetSystem = document.getElementById('btn-reset-system');
    const promptChips = document.querySelectorAll('.chip');
    
    // Modal
    const btnUpload = document.getElementById('btn-upload');
    const modal = document.getElementById('upload-modal');
    const btnCloseModal = document.getElementById('close-modal');
    const btnSubmitUpload = document.getElementById('btn-submit-upload');
    const uploadStatus = document.getElementById('upload-status');
    const uploadTitle = document.getElementById('upload-title');
    const uploadContent = document.getElementById('upload-content');
    
    // Admin Modal Elements
    const btnAdmin = document.getElementById('btn-admin');
    const adminModal = document.getElementById('admin-modal');
    const closeAdminModal = document.getElementById('close-admin-modal');
    const adminBody = document.getElementById('admin-body');

    // Theme Toggle Logic
    const SUN_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
    const MOON_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9.01 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;

    const btnThemeToggle = document.getElementById('btn-theme-toggle');
    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-theme');
        if (btnThemeToggle) btnThemeToggle.innerHTML = SUN_SVG;
    } else {
        if (btnThemeToggle) btnThemeToggle.innerHTML = MOON_SVG;
    }
    
    if (btnThemeToggle) {
        btnThemeToggle.addEventListener('click', () => {
            btnThemeToggle.classList.add('rotating');
            setTimeout(() => {
                document.body.classList.toggle('dark-theme');
                if (document.body.classList.contains('dark-theme')) {
                    localStorage.setItem('theme', 'dark');
                    btnThemeToggle.innerHTML = SUN_SVG;
                } else {
                    localStorage.setItem('theme', 'light');
                    btnThemeToggle.innerHTML = MOON_SVG;
                }
                setTimeout(() => btnThemeToggle.classList.remove('rotating'), 50);
            }, 300);
        });
    }

    // Logout Logic
    const btnLogout = document.getElementById('btn-logout');
    if (btnLogout) {
        btnLogout.addEventListener('click', () => {
            window.location.href = '/';
        });
    }

    const HR_QUERY = "Find employee handbook section 7.3";

    // Chart.js Setup
    const ctx = document.getElementById('metricsChart').getContext('2d');
    const metricsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [], // Timestamps or Run #
            datasets: [
                {
                    label: 'Latency (s)',
                    data: [],
                    borderColor: '#1A73E8', // Google Blue
                    borderWidth: 2,
                    tension: 0.4, // Smooth elegant curve
                    pointRadius: 4,
                    pointBackgroundColor: '#FFFFFF',
                    yAxisID: 'y'
                },
                {
                    label: 'Cost ($)',
                    data: [],
                    borderColor: '#1E8E3E', // Google Green
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: '#FFFFFF',
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false } // Minimalist - no legend
            },
            scales: {
                x: {
                    display: false // Hide grid and labels
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    grid: { display: false },
                    title: { display: true, text: 'Latency (s)', color: '#767068' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: { display: false },
                    title: { display: true, text: 'Cost ($)', color: '#6B8068' }
                }
            }
        }
    });

    function updateChart(events) {
        // Filter events that actually contain execution metrics
        const executionEvents = events.filter(e => e.type === 'system' && e.metrics && e.metrics.latency !== undefined);
        
        // Map to data arrays
        const labels = executionEvents.map((_, i) => `Run ${i + 1}`);
        const latencies = executionEvents.map(e => e.metrics.latency);
        const costs = executionEvents.map(e => e.metrics.cost);
        
        metricsChart.data.labels = labels;
        metricsChart.data.datasets[0].data = latencies;
        metricsChart.data.datasets[1].data = costs;
        metricsChart.update();
    }

    // Initialize Memory Table and Timeline on load
    fetchMemory();
    fetchTimeline();

    // Set an interval to poll timeline for updates
    setInterval(fetchTimeline, 2000);

    // Modal Event Listeners
    btnUpload.addEventListener('click', () => {
        modal.classList.remove('hidden');
        uploadStatus.classList.add('hidden');
    });

    btnCloseModal.addEventListener('click', () => {
        modal.classList.add('hidden');
    });
    
    // Admin Modal listeners
    btnAdmin.addEventListener('click', async () => {
        adminModal.classList.remove('hidden');
        await fetchDocuments();
    });
    
    closeAdminModal.addEventListener('click', () => {
        adminModal.classList.add('hidden');
    });

    btnSubmitUpload.addEventListener('click', async () => {
        const title = uploadTitle.value.trim();
        const content = uploadContent.value.trim();
        if (!title || !content) return;

        btnSubmitUpload.disabled = true;
        btnSubmitUpload.textContent = 'Ingesting...';

        try {
            const res = await fetch('/api/upload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: title, content: content })
            });
            const data = await res.json();
            
            if (data.status === 'success') {
                uploadStatus.textContent = `Success! Keywords extracted: ${data.keywords.join(', ')}`;
                uploadStatus.classList.remove('hidden');
                
                // UX Fix: Clear the fields!
                uploadTitle.value = '';
                uploadContent.value = '';
                
                setTimeout(() => { modal.classList.add('hidden'); }, 2000);
            }
        } catch (e) {
            console.error(e);
            uploadStatus.textContent = `Error uploading document.`;
            uploadStatus.classList.remove('hidden');
        } finally {
            btnSubmitUpload.disabled = false;
            btnSubmitUpload.textContent = 'Ingest & Extract Keywords';
        }
    });

    // Event Listeners
    btnResetSystem.addEventListener('click', async () => {
        if(confirm("Reset the Economic Memory Database?")) {
            await fetch('/api/reset', { method: 'POST' });
            chatWindow.innerHTML = '<div class="message system">Memory reset. Ready for Demo.</div>';
            valLatency.textContent = '--';
            valCost.textContent = '--';
            fetchMemory();
            fetchTimeline();
        }
    });

    promptChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const query = chip.getAttribute('data-query');
            if (query) {
                const queryInput = document.getElementById('query-input');
                queryInput.value = query;
                document.getElementById('btn-send').click();
            }
        });
    });

    const queryInput = document.getElementById('query-input');
    const btnSend = document.getElementById('btn-send');

    btnSend.addEventListener('click', () => {
        const query = queryInput.value.trim();
        if (query) {
            addMessage(query, 'user');
            sendQuery(query);
            queryInput.value = '';
        }
    });

    queryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            btnSend.click();
        }
    });

    btnRunAuditor.addEventListener('click', async () => {
        btnRunAuditor.textContent = "Auditing...";
        btnRunAuditor.disabled = true;
        
        try {
            const res = await fetch('/api/audit', { method: 'POST' });
            const data = await res.json();
            
            if(data.status === 'success') {
                addMessage(`⚠️ AUDIT COMPLETE: Phoenix trace analysis found hidden LLM tool failures. Correcting memory...`, 'system');
                renderMemoryTable(data.data, true); // highlight changes
                fetchTimeline(); // Force immediate timeline update
            }
        } catch (e) {
            console.error(e);
            addMessage(`Error running audit.`, 'system');
        } finally {
            btnRunAuditor.textContent = "Run Phoenix Auditor";
            btnRunAuditor.disabled = false;
        }
    });

    // Helper Functions
    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.className = `message ${sender}`;
        div.textContent = text;
        chatWindow.appendChild(div);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    async function sendQuery(query) {
        promptChips.forEach(c => c.disabled = true);
        addMessage("Executing query through ADK Orchestrator...", 'system');

        try {
            const res = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });
            const data = await res.json();
            
            if(data.status === 'success') {
                // Update Chat
                addMessage(data.response.result_text, 'agent');
                
                // Update Decision Panel
                const decisionPanel = document.getElementById('decision-panel');
                const decisionContent = document.getElementById('decision-content');
                let scoresHtml = "";
                if (data.response.routing && data.response.routing.all_options && data.response.routing.all_options.length > 0) {
                    const sortedOpts = data.response.routing.all_options.sort((a,b) => b.confidence - a.confidence);
                    scoresHtml = sortedOpts.map(opt => `<div style="display:flex; justify-content:space-between; max-width:250px;"><span>${opt.tool}</span><span style="font-family:monospace; color:var(--text-secondary);">${opt.confidence.toFixed(2)}</span></div>`).join('');
                } else {
                    scoresHtml = `<div style="display:flex; justify-content:space-between; max-width:250px;"><span>${data.response.routing.tool} (Default)</span><span style="font-family:monospace; color:var(--text-secondary);">0.50</span></div>`;
                }
                
                decisionContent.innerHTML = `
                    <div style="margin-bottom:0.5rem; font-style:italic;">Query: "${query}"</div>
                    <div style="margin-bottom:0.3rem; font-weight:600; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.5px; color:var(--text-secondary);">Tool Scores</div>
                    <div style="background:var(--bg-secondary); padding:0.8rem; border-radius:6px; margin-bottom:0.8rem; border:1px solid var(--border);">
                        ${scoresHtml}
                    </div>
                    <div><strong>Selected Route:</strong> <span style="color:var(--google-blue); font-weight:600;">${data.response.routing.tool}</span></div>
                `;
                decisionPanel.classList.remove('hidden');

                // Update Delta Cards
                const m = data.response.metrics;
                valLatency.textContent = `${m.latency.toFixed(2)}s`;
                valCost.textContent = `$${m.cost.toFixed(3)}`;
                
                // Refresh memory table and timeline
                fetchMemory();
                fetchTimeline();
            }
        } catch (e) {
            console.error(e);
            addMessage(`Error connecting to orchestrator.`, 'system');
        } finally {
            promptChips.forEach(c => c.disabled = false);
        }
    }

    async function fetchMemory() {
        try {
            const res = await fetch('/api/memory');
            const data = await res.json();
            if(data.status === 'success') {
                renderMemoryTable(data.data, false);
            }
        } catch (e) {
            console.error(e);
        }
    }

    async function fetchTimeline() {
        try {
            const res = await fetch('/api/timeline');
            const events = await res.json();
            renderTimeline(events);
            updateChart(events); // Update the visual graph
        } catch (e) {
            console.error(e);
        }
    }

    function renderTimeline(events) {
        if(events.length === 0) {
            timelineContainer.innerHTML = '<div class="timeline-empty">Awaiting events...</div>';
            return;
        }

        timelineContainer.innerHTML = '';
        // Render events in reverse chronological order
        const sortedEvents = [...events].reverse();
        
        sortedEvents.forEach(evt => {
            const div = document.createElement('div');
            div.className = `timeline-event type-${evt.type}`;
            
            const timeStr = new Date(evt.timestamp).toLocaleTimeString();
            
            let metricsHtml = '';
            if (evt.metrics) {
                const parts = [];
                if (evt.metrics.latency !== undefined) parts.push(`Lat: ${evt.metrics.latency.toFixed(2)}s`);
                if (evt.metrics.cost !== undefined) parts.push(`Cost: $${evt.metrics.cost.toFixed(3)}`);
                if (evt.metrics.corrections !== undefined) parts.push(`Fixes: ${evt.metrics.corrections}`);
                if (evt.metrics.mode !== undefined) parts.push(`Mode: ${evt.metrics.mode.toUpperCase()}`);
                if (parts.length > 0) {
                    metricsHtml = `<div class="event-metrics">${parts.join(' | ')}</div>`;
                }
            }

            div.innerHTML = `
                <div class="event-time">${timeStr}</div>
                <div class="event-title">${evt.title}</div>
                <div class="event-desc">${evt.description}</div>
                ${metricsHtml}
            `;
            timelineContainer.appendChild(div);
        });
    }

    function renderMemoryTable(rows, flash = false) {
        memoryBody.innerHTML = '';
        if(rows.length === 0) {
            memoryBody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--text-secondary)">No data yet. Run queries.</td></tr>';
            return;
        }

        rows.forEach(row => {
            const tr = document.createElement('tr');
            if (flash && row.delta < 0) {
                tr.classList.add('highlight-row');
            }
            
            let confClass = 'conf-high';
            let confIcon = '🟢';
            if (row.confidence < 0.4) { confClass = 'conf-low'; confIcon = '🔴'; }
            else if (row.confidence < 0.7) { confClass = 'conf-med'; confIcon = '🟡'; }

            const successRate = (row.success_rate * 100).toFixed(0);
            
            let deltaHtml = '--';
            if (row.delta !== undefined && Math.abs(row.delta) > 0.01) {
                if (row.delta > 0) {
                    deltaHtml = `<span class="delta-up">↑ ${row.delta.toFixed(2)}</span>`;
                } else {
                    deltaHtml = `<span class="delta-down">↓ ${Math.abs(row.delta).toFixed(2)}</span>`;
                }
            }

            tr.innerHTML = `
                <td>${row.category}</td>
                <td>${row.tool}</td>
                <td>${row.runs}</td>
                <td>${successRate}%</td>
                <td class="${confClass}">${confIcon} ${row.confidence.toFixed(2)}</td>
                <td>${deltaHtml}</td>
            `;
            memoryBody.appendChild(tr);
        });
    }

    async function fetchDocuments() {
        try {
            const res = await fetch('/api/documents');
            const data = await res.json();
            
            adminBody.innerHTML = '';
            if(!data.data || data.data.length === 0) {
                adminBody.innerHTML = '<tr><td colspan="3" style="text-align:center; color:var(--text-secondary)">No documents ingested yet.</td></tr>';
                return;
            }
            
            data.data.forEach(doc => {
                const tr = document.createElement('tr');
                const keywordsHtml = doc.keywords.map(kw => `<span style="background:var(--bg-hover); color:var(--google-blue); padding:2px 6px; border-radius:4px; font-size:0.8rem; margin-right:4px;">${kw}</span>`).join('');
                tr.innerHTML = `
                    <td style="font-weight:500;">${doc.title}</td>
                    <td>${keywordsHtml}</td>
                    <td style="color:var(--text-secondary); font-size:0.85rem;">${doc.content}</td>
                `;
                adminBody.appendChild(tr);
            });
        } catch (e) {
            console.error(e);
        }
    }
});
