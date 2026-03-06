/**
 * Core Web Vitals best practices:
 * - This file should be loaded with `<script src="/static/js/app.js" defer></script>` to prevent render-blocking.
 * - Event listeners are added after DOM load.
 */

document.addEventListener('DOMContentLoaded', () => {
    let allMessages = [];
    
    let currentFilter = 'ALL';
    let timeFilter = sessionStorage.getItem('timeFilter') || '1';
    let searchQuery = '';

    // --- State ---
    let activeMessageId = null;

    // --- Elements ---
    const lockScreen = document.getElementById('lock-screen');
    const mainApp = document.getElementById('main-app');
    const lockBtn = document.getElementById('lock-btn');
    const unlockBtn = document.getElementById('unlock-btn');
    const passwordInput = document.getElementById('unlock-password');
    const unlockError = document.getElementById('unlock-error');
    const messageContainer = document.getElementById('message-container');
    const replyInput = document.getElementById('reply-input');
    const replyBtn = document.getElementById('reply-submit-btn');
    const aiContextPanel = document.getElementById('ai-context-panel');
    const summarizeBtn = document.getElementById('summarize-btn');

    // --- Modals ---
    const addPlatformBtn = document.getElementById('add-platform-btn');
    const platformModal = document.getElementById('platform-setup-modal');
    const closePlatformModal = document.getElementById('close-platform-modal');
    const platformForm = document.getElementById('platform-form');

    // --- 1. LOCK SCREEN LOGIC ---
    if (localStorage.getItem('isLocked') === 'true') {
        applyLockState();
    }

    function applyLockState() {
        lockScreen.classList.remove('hidden');
        lockScreen.classList.add('flex');
        mainApp.classList.add('blur-sm', 'pointer-events-none', 'select-none');
        passwordInput.value = '';
        if (document.activeElement !== passwordInput) {
            setTimeout(() => passwordInput.focus(), 100);
        }
    }

    function applyUnlockState() {
        lockScreen.classList.add('hidden');
        lockScreen.classList.remove('flex');
        mainApp.classList.remove('blur-sm', 'pointer-events-none', 'select-none');
        unlockError.classList.add('hidden');
    }

    lockBtn.addEventListener('click', () => {
        localStorage.setItem('isLocked', 'true');
        applyLockState();
    });

    unlockBtn.addEventListener('click', async () => {
        const password = passwordInput.value;
        if (!password) return;

        try {
            const formData = new URLSearchParams();
            formData.append('username', window.CURRENT_USER || 'discgolf_admin');
            formData.append('password', password);

            const response = await fetch('/token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });

            if (response.ok) {
                localStorage.setItem('isLocked', 'false');
                applyUnlockState();
            } else {
                unlockError.classList.remove('hidden');
            }
        } catch (error) {
            console.error("Unlock failed", error);
            unlockError.classList.remove('hidden');
        }
    });

    passwordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') unlockBtn.click();
    });

        // --- 2. FETCH MESSAGES & RENDER ---
    async function fetchMessages(filterPlatform = currentFilter) {
        currentFilter = filterPlatform;
        try {
            const response = await fetch(`/api/messages?hours=${timeFilter}`);
            const messages = await response.json();
            if (!response.ok) {
                throw new Error(messages.detail || 'Failed to load messages from server');
            }
            allMessages = messages;
            renderMessages();
        } catch (e) {
            console.error("Failed to load messages", e);
            messageContainer.innerHTML = `<div class="text-red-500 p-4">Failed to load messages: ${e.message}</div>`;
        }
    }

    function renderMessages() {
        let filteredMessages = currentFilter === 'ALL' 
            ? allMessages 
            : allMessages.filter(msg => msg.platform === currentFilter);

        if (searchQuery) {
            const lowerQuery = searchQuery.toLowerCase();
            filteredMessages = filteredMessages.filter(msg => 
                (msg.sender_name && msg.sender_name.toLowerCase().includes(lowerQuery)) ||
                (msg.content && msg.content.toLowerCase().includes(lowerQuery)) ||
                (msg.platform && msg.platform.toLowerCase().includes(lowerQuery))
            );
        }

        if (filteredMessages.length === 0) {
            messageContainer.innerHTML = `
                <div class="flex flex-col items-center justify-center h-full text-gray-500 space-y-4">
                    <i class="fa-solid fa-inbox text-4xl"></i>
                    <p>${allMessages.length === 0 ? 'No messages found in database. Connect platforms to begin.' : 'No messages match your search/filter.'}</p>
                </div>
            `;
            return;
        }

        messageContainer.innerHTML = '';

        filteredMessages.forEach(msg => {
            let iconClass = 'fa-comment';
            let iconColor = 'text-gray-400';
            if(msg.platform === 'INSTAGRAM' || msg.platform === 'FACEBOOK') { iconClass = 'fa-instagram fa-brands'; iconColor = 'text-pink-500'; }
            if(msg.platform === 'YOUTUBE') { iconClass = 'fa-youtube fa-brands'; iconColor = 'text-red-500'; }
            if(msg.platform === 'DISCORD') { iconClass = 'fa-discord fa-brands'; iconColor = 'text-[#5865F2]'; }
            if(msg.platform === 'TIKTOK') { iconClass = 'fa-tiktok fa-brands'; iconColor = 'text-white'; }

            const d = new Date(msg.timestamp);
            const timeString = d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

            const msgDiv = document.createElement('div');
            msgDiv.className = `flex hover:bg-[#2B2D31] p-2 -mx-2 rounded transition-colors group cursor-pointer ${msg.is_read ? 'opacity-70' : ''}`;
            msgDiv.dataset.id = msg.id;

            msgDiv.dataset.summary = msg.ai_summary || "No AI summary generated yet.";
            msgDiv.dataset.priority = msg.ai_priority_score || "N/A";
            msgDiv.dataset.sender = msg.sender_name;
            msgDiv.dataset.platform = msg.platform;

            let priorityBadge = '';
            if (msg.ai_priority_score && msg.ai_priority_score >= 8) {
                priorityBadge = `<span class="bg-red-500/20 text-red-400 text-[10px] px-2 py-0.5 rounded ml-2 font-bold"><i class="fa-solid fa-fire text-[10px]"></i> HOT</span>`;
            }

            let avatarHtml = msg.sender_avatar_url 
                ? `<img src="${msg.sender_avatar_url}" class="w-8 h-8 rounded-full object-cover">`
                : `<div class="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center"><i class="fa-solid fa-user text-gray-300 text-xs"></i></div>`;

            msgDiv.innerHTML = `
                <div class="flex items-start mr-3 mt-1">
                    <i class="${iconClass} ${iconColor} text-[14px] mr-2 mt-2"></i>
                    ${avatarHtml}
                </div>
                <div class="flex-1">
                    <div class="flex items-baseline space-x-2">
                        <span class="font-bold text-green-400">${msg.sender_name}</span>
                        <span class="text-[10px] uppercase bg-gray-800 px-1.5 py-0.5 rounded text-gray-400">${msg.platform_custom_name || msg.platform}</span>
                        ${msg.platform === 'DISCORD' && msg.channel_name && msg.channel_name !== 'unknown' ? `<span class="text-[10px] uppercase bg-gray-800 px-1.5 py-0.5 rounded text-gray-400">#${msg.channel_name}</span>` : ''}
                        <span class="text-xs text-gray-400">${timeString}</span>
                        ${priorityBadge}
                    </div>
                    <div class="text-gray-300 text-sm mt-1 leading-relaxed">
                        ${msg.content}
                    </div>
                    ${msg.ai_summary ? `<div class="text-emerald-400 text-xs mt-1"><i class="fa-solid fa-robot mr-1"></i> ${msg.ai_summary}</div>` : ''}
                </div>
            `;

            msgDiv.addEventListener('click', () => selectMessage(msgDiv));
            messageContainer.appendChild(msgDiv);
        });
    }

    // Add UI handlers for search and time filter
    const timeFilterEl = document.getElementById('time-filter');
    const searchInputEl = document.getElementById('search-input');

    if (timeFilterEl) {
        timeFilterEl.value = timeFilter;
        timeFilterEl.addEventListener('change', (e) => {
            timeFilter = e.target.value;
            sessionStorage.setItem('timeFilter', timeFilter);
            fetchMessages(); // re-fetch from server with new time constraint
        });
    }

    if (searchInputEl) {
        searchInputEl.addEventListener('input', (e) => {
            searchQuery = e.target.value;
            renderMessages(); // only re-render local data
        });
    }

    function selectMessage(msgElement) {
        document.querySelectorAll('#message-container > div').forEach(el => {
            el.classList.remove('bg-[#2B2D31]', 'border-l-2', 'border-emerald-500');
        });

        msgElement.classList.add('bg-[#2B2D31]', 'border-l-2', 'border-emerald-500');
        activeMessageId = msgElement.dataset.id;
        
        replyInput.disabled = false;
        replyBtn.disabled = false;
        replyInput.placeholder = `Reply to ${msgElement.dataset.sender}...`;
        replyInput.focus();

        const platform = msgElement.dataset.platform;
        let pColor = 'text-gray-400';
        if (platform === 'INSTAGRAM' || platform === 'FACEBOOK') pColor = 'text-pink-500';
        if (platform === 'YOUTUBE') pColor = 'text-red-500';
        if (platform === 'DISCORD') pColor = 'text-[#5865F2]';
        if (platform === 'TIKTOK') pColor = 'text-white';

        if (aiContextPanel) {
            aiContextPanel.innerHTML = `
                <div class="h-full flex flex-col">
                    <div class="flex items-center space-x-3 mb-6">
                        <div class="w-12 h-12 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0">
                            <i class="fa-solid fa-user text-xl"></i>
                        </div>
                        <div>
                            <div class="font-bold text-lg text-white">${msgElement.dataset.sender}</div>
                            <div class="text-xs font-bold uppercase ${pColor}">${platform}</div>
                        </div>
                    </div>

                    <div class="bg-[#1E1F22] rounded p-4 mb-4 border border-gray-800">
                        <div class="text-xs font-bold text-gray-500 uppercase mb-2"><i class="fa-solid fa-robot mr-1"></i> AI Summary</div>
                        <div class="text-sm text-gray-300 leading-relaxed">${msgElement.dataset.summary}</div>
                    </div>

                    <div class="bg-[#1E1F22] rounded p-4 border border-gray-800">
                        <div class="text-xs font-bold text-gray-500 uppercase mb-2"><i class="fa-solid fa-chart-line mr-1"></i> Priority Score</div>
                        <div class="text-2xl font-bold ${msgElement.dataset.priority >= 8 ? 'text-red-400' : 'text-green-400'}">${msgElement.dataset.priority}/10</div>
                    </div>
                </div>
            `;
        }
    }

    const sidebarTabs = document.querySelectorAll('.sidebar-tab');
    const centerHeaderIcon = document.getElementById('center-header-icon');
    const centerHeaderText = document.getElementById('center-header-text');

    sidebarTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active state from all
            sidebarTabs.forEach(t => {
                t.classList.remove('bg-[#3F4147]', 'text-gray-200');
                t.classList.add('text-gray-400');
            });
            
            // Add active state to clicked
            tab.classList.add('bg-[#3F4147]', 'text-gray-200');
            tab.classList.remove('text-gray-400');

            const filter = tab.dataset.filter;
            const iconClass = tab.dataset.icon;
            const title = tab.dataset.title;

            if (centerHeaderIcon && centerHeaderText) {
                centerHeaderIcon.className = `${iconClass} w-5 text-center mr-2`;
                centerHeaderText.textContent = title;
            }

            fetchMessages(filter);
        });
    });

// --- 3. REPLY LOGIC ---
    replyBtn.addEventListener('click', async () => {
        if (!activeMessageId || !replyInput.value.trim()) return;

        const content = replyInput.value.trim();
        const originalText = replyBtn.innerHTML;
        replyBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin text-emerald-400"></i>';
        replyBtn.disabled = true;

        try {
            const response = await fetch(`/api/messages/${activeMessageId}/reply`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content })
            });

            if (response.ok) {
                replyInput.value = '';
                replyInput.placeholder = 'Reply sent successfully!';
                setTimeout(() => replyInput.placeholder = 'Select a message to reply...', 2000);
                fetchMessages(); // refresh to update read status
            } else {
                const err = await response.json();
                alert(`Error sending reply: ${err.detail}`);
            }
        } catch (e) {
            alert('Network error sending reply');
        } finally {
            replyBtn.innerHTML = originalText;
            replyBtn.disabled = false;
        }
    });

    replyInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') replyBtn.click();
    });

    // --- 4. AI SUMMARIZATION ---
    if (summarizeBtn) {
        summarizeBtn.addEventListener('click', async () => {
            const originalIcon = summarizeBtn.innerHTML;
            summarizeBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
            try {
                const response = await fetch('/api/ai/summarize', { method: 'POST' });
                const result = await response.json();
                if (result.status === 'success') {
                    console.log(`Summarized ${result.processed_count} messages`);
                    fetchMessages();
                }
            } catch (e) {
                console.error("Failed to run summarization", e);
            } finally {
                summarizeBtn.innerHTML = originalIcon;
            }
        });
    }

    
    // --- 6. SETTINGS & PROFILE ---
    const settingsGear = document.getElementById('settings-gear');
    const settingsPopover = document.getElementById('settings-popover');
    const openSettingsBtn = document.getElementById('open-settings-btn');
    const signOutBtn = document.getElementById('sign-out-btn');
    
    // Toggle popover
    if (settingsGear) {
        settingsGear.addEventListener('click', (e) => {
            e.stopPropagation();
            settingsPopover.classList.toggle('hidden');
        });
    }

    // Hide popover when clicking outside
    document.addEventListener('click', (e) => {
        if (settingsPopover && !settingsPopover.contains(e.target) && e.target !== settingsGear) {
            settingsPopover.classList.add('hidden');
        }
    });

    // Sign out
    if (signOutBtn) {
        signOutBtn.addEventListener('click', async () => {
            await fetch('/logout', { method: 'POST' });
            localStorage.removeItem('isLocked'); // Reset lock state
            window.location.href = '/login';
        });
    }

    // Settings Modal UI & Tabs
    const settingsModal = document.getElementById('user-settings-modal');
    const closeSettingsBtn = document.getElementById('close-settings-modal');
    
    const settingsTabBtns = document.querySelectorAll('.settings-tab-btn');
    const settingsContents = document.querySelectorAll('.settings-content');

    if (openSettingsBtn) {
        openSettingsBtn.addEventListener('click', () => {
            settingsPopover.classList.add('hidden');
            settingsModal.classList.remove('hidden');
            // reset to account tab by default
            document.querySelector('.settings-tab-btn[data-tab="account"]').click();
        });
    }

    if (closeSettingsBtn) {
        closeSettingsBtn.addEventListener('click', () => {
            settingsModal.classList.add('hidden');
        });
    }

    // Tab Switching Logic
    settingsTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            
            // update buttons
            settingsTabBtns.forEach(b => {
                b.classList.remove('active', 'text-gray-200', 'bg-[#3F4147]');
                b.classList.add('text-gray-400');
            });
            btn.classList.add('active', 'text-gray-200', 'bg-[#3F4147]');
            btn.classList.remove('text-gray-400');

            // show content
            settingsContents.forEach(content => {
                content.classList.add('hidden');
            });
            document.getElementById(`settings-${tabId}-tab`).classList.remove('hidden');

            if (tabId === 'logs') {
                fetchLogs();
            }
        });
    });

    // Account Form Logic (Username / Password)
    const settingsForm = document.getElementById('user-settings-form');
    const sUsername = document.getElementById('settings-username');
    const sUsernameMsg = document.getElementById('settings-username-msg');
    const sPassword = document.getElementById('settings-password');
    const sPasswordReqs = document.getElementById('settings-password-reqs');
    const sConfirm = document.getElementById('settings-confirm-password');
    const sConfirmMsgContainer = document.getElementById('settings-confirm-msg-container');
    const sConfirmIcon = document.getElementById('settings-confirm-icon');
    const sConfirmMsg = document.getElementById('settings-confirm-msg');
    const sSubmit = document.getElementById('settings-submit-btn');
    const sStatus = document.getElementById('settings-status-message');

    let isSUsernameValid = true;
    let isSPasswordValid = true;
    let isSConfirmValid = true;
    let sUsernameTimer;
    const currentUsername = window.CURRENT_USER;

    const checkSettingsFormValidity = () => {
        sSubmit.disabled = !(isSUsernameValid && isSPasswordValid && isSConfirmValid);
    };

    if (sUsername) {
        sUsername.addEventListener('input', (e) => {
            clearTimeout(sUsernameTimer);
            const val = e.target.value.trim();
            if (val === currentUsername) {
                isSUsernameValid = true;
                sUsernameMsg.classList.add('hidden');
                sUsername.className = 'w-full bg-[#313338] text-white p-2 rounded outline-none border border-gray-800 focus:ring-2 focus:ring-emerald-500';
                checkSettingsFormValidity();
                return;
            }
            if (val.length < 3 || val.length > 20 || !/^[a-zA-Z0-9_]+$/.test(val)) {
                isSUsernameValid = false;
                sUsernameMsg.textContent = '3-20 characters, alphanumeric and underscores only';
                sUsernameMsg.className = 'text-xs mt-1 text-red-500';
                sUsername.className = 'w-full bg-[#313338] text-white p-2 rounded outline-none border border-red-500 focus:ring-2 focus:ring-red-500';
                sUsernameMsg.classList.remove('hidden');
                checkSettingsFormValidity();
                return;
            }
            sUsernameMsg.textContent = 'Checking availability...';
            sUsernameMsg.className = 'text-xs mt-1 text-gray-400';
            sUsernameMsg.classList.remove('hidden');
            sUsernameTimer = setTimeout(async () => {
                try {
                    const response = await fetch(`/check-username?username=${encodeURIComponent(val)}`);
                    const data = await response.json();
                    if (data.available) {
                        isSUsernameValid = true;
                        sUsernameMsg.innerHTML = '<i class="fa-solid fa-check text-green-500 mr-1"></i><span class="text-green-500">Username is available!</span>';
                        sUsername.className = 'w-full bg-[#313338] text-white p-2 rounded outline-none border border-green-500 focus:ring-2 focus:ring-green-500';
                    } else {
                        isSUsernameValid = false;
                        sUsernameMsg.innerHTML = `<i class="fa-solid fa-xmark text-red-500 mr-1"></i><span class="text-red-500">Taken.</span>`;
                        sUsername.className = 'w-full bg-[#313338] text-white p-2 rounded outline-none border border-red-500 focus:ring-2 focus:ring-red-500';
                    }
                    checkSettingsFormValidity();
                } catch (err) {
                    sUsernameMsg.classList.add('hidden');
                }
            }, 500);
        });
    }

    const updateSetReq = (id, isValid) => {
        const el = document.getElementById(id);
        if (isValid) {
            el.innerHTML = '<i class="fa-solid fa-circle-check text-green-500 mr-1.5 w-3 text-center"></i>' + el.textContent.trim();
            el.classList.add('text-gray-300');
            el.classList.remove('text-gray-400');
        } else {
            el.innerHTML = '<i class="fa-solid fa-circle-xmark text-red-500 mr-1.5 w-3 text-center"></i>' + el.textContent.trim();
            el.classList.remove('text-gray-300');
            el.classList.add('text-gray-400');
        }
        return isValid;
    };

    if (sPassword) {
        sPassword.addEventListener('input', (e) => {
            const val = e.target.value;
            if (val === '') {
                sPasswordReqs.classList.add('hidden');
                sConfirm.disabled = true;
                sConfirm.value = '';
                sConfirmMsgContainer.classList.add('hidden');
                isSPasswordValid = true;
                isSConfirmValid = true;
                checkSettingsFormValidity();
                return;
            }
            sPasswordReqs.classList.remove('hidden');
            sConfirm.disabled = false;
            const reqLength = updateSetReq('set-req-length', val.length >= 8);
            const reqUpper = updateSetReq('set-req-upper', /[A-Z]/.test(val));
            const reqLower = updateSetReq('set-req-lower', /[a-z]/.test(val));
            const reqNumber = updateSetReq('set-req-number', /\d/.test(val));
            const reqSpecial = updateSetReq('set-req-special', /[^a-zA-Z0-9]/.test(val));
            isSPasswordValid = reqLength && reqUpper && reqLower && reqNumber && reqSpecial;
            if (sConfirm.value) {
                isSConfirmValid = (val === sConfirm.value);
                sConfirmMsgContainer.classList.remove('hidden');
                if (isSConfirmValid) {
                    sConfirmIcon.className = 'fa-solid fa-circle-check text-green-500 mr-1';
                    sConfirmMsg.textContent = 'Passwords match';
                    sConfirmMsg.className = 'text-green-500';
                    sConfirm.className = 'w-full bg-[#313338] text-white p-2 rounded outline-none border border-green-500 focus:ring-2 focus:ring-green-500';
                } else {
                    sConfirmIcon.className = 'fa-solid fa-circle-xmark text-red-500 mr-1';
                    sConfirmMsg.textContent = 'Passwords do not match';
                    sConfirmMsg.className = 'text-red-400';
                    sConfirm.className = 'w-full bg-[#313338] text-white p-2 rounded outline-none border border-red-500 focus:ring-2 focus:ring-red-500';
                }
            } else {
                isSConfirmValid = false;
            }
            checkSettingsFormValidity();
        });
    }

    if (sConfirm) {
        sConfirm.addEventListener('input', (e) => {
            const val = e.target.value;
            sConfirmMsgContainer.classList.remove('hidden');
            isSConfirmValid = (sPassword.value === val);
            if (isSConfirmValid) {
                sConfirmIcon.className = 'fa-solid fa-circle-check text-green-500 mr-1';
                sConfirmMsg.textContent = 'Passwords match';
                sConfirmMsg.className = 'text-green-500';
                sConfirm.className = 'w-full bg-[#313338] text-white p-2 rounded outline-none border border-green-500 focus:ring-2 focus:ring-green-500';
            } else {
                sConfirmIcon.className = 'fa-solid fa-circle-xmark text-red-500 mr-1';
                sConfirmMsg.textContent = 'Passwords do not match';
                sConfirmMsg.className = 'text-red-400';
                sConfirm.className = 'w-full bg-[#313338] text-white p-2 rounded outline-none border border-red-500 focus:ring-2 focus:ring-red-500';
            }
            checkSettingsFormValidity();
        });
    }

    if (settingsForm) {
        settingsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const originalText = sSubmit.innerHTML;
            sSubmit.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';
            sSubmit.disabled = true;
            sStatus.classList.add('hidden');
            const newUsername = sUsername.value.trim();
            const newPassword = sPassword.value;
            const payload = {};
            if (newUsername !== currentUsername) payload.username = newUsername;
            if (newPassword !== '') payload.password = newPassword;

            try {
                const response = await fetch('/api/users/me', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (response.ok) {
                    sStatus.textContent = 'Account Updated! Reloading...';
                    sStatus.className = 'text-sm rounded p-3 text-center font-bold bg-green-500/20 text-green-400 border border-green-500/30 mt-4';
                    sStatus.classList.remove('hidden');
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    const err = await response.json();
                    sStatus.textContent = `Update Failed: ${err.detail || 'Invalid data'}`;
                    sStatus.className = 'text-sm rounded p-3 text-center font-bold bg-red-500/20 text-red-400 border border-red-500/30 mt-4';
                    sStatus.classList.remove('hidden');
                    sSubmit.innerHTML = originalText;
                    sSubmit.disabled = false;
                }
            } catch (error) {
                sStatus.textContent = 'Network error.';
                sStatus.className = 'text-sm rounded p-3 text-center font-bold bg-red-500/20 text-red-400 border border-red-500/30 mt-4';
                sStatus.classList.remove('hidden');
                sSubmit.innerHTML = originalText;
                sSubmit.disabled = false;
            }
        });
    }

    // Delete Account Flow
    const deleteAccountBtn = document.getElementById('delete-account-btn');
    const deleteAccountModal = document.getElementById('delete-account-modal');
    const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');

    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', (e) => {
            e.preventDefault();
            deleteAccountModal.classList.remove('hidden');
            deleteAccountModal.classList.add('flex');
        });
    }

    if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', () => {
            deleteAccountModal.classList.add('hidden');
            deleteAccountModal.classList.remove('flex');
        });
    }

    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', async () => {
            confirmDeleteBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Deleting...';
            confirmDeleteBtn.disabled = true;
            cancelDeleteBtn.disabled = true;
            // Show main loading indicator
            const loadingOverlay = document.getElementById('loading-overlay');
            const loadingText = document.getElementById('loading-text');
            loadingText.textContent = "Deleting account and all data...";
            loadingOverlay.classList.remove("hidden");
            loadingOverlay.classList.add("flex");
            document.getElementById('main-app').classList.add("blur-sm");

            try {
                const response = await fetch('/api/users/me', { method: 'DELETE' });
                if (response.ok) {
                    window.location.href = '/login';
                } else {
                    alert("Failed to delete account.");
                    window.location.reload();
                }
            } catch (e) {
                alert("Network error.");
                window.location.reload();
            }
        });
    }

    // AI Settings Flow
    const aiProviderSelect = document.getElementById('ai-provider-select');
    const aiInstructions = document.getElementById('ai-instructions');
    const aiTokenInput = document.getElementById('ai-token-input');
    const aiSubmitBtn = document.getElementById('ai-submit-btn');
    const aiStatusMessage = document.getElementById('ai-status-message');
    const aiSettingsForm = document.getElementById('ai-settings-form');

    const updateAiInstructions = () => {
        const p = aiProviderSelect.value;
        if (p === 'gemini') {
            aiInstructions.innerHTML = `<h4 class="font-bold text-emerald-400 mb-2"><i class="fa-solid fa-circle-info"></i> How to connect Gemini</h4>
                <p>Get an API key from Google AI Studio. <a href="https://aistudio.google.com/app/apikey" target="_blank" class="text-blue-400 hover:underline">Get an API key here.</a></p>`;
        } else if (p === 'openai') {
            aiInstructions.innerHTML = `<h4 class="font-bold text-emerald-400 mb-2"><i class="fa-solid fa-circle-info"></i> How to connect OpenAI</h4>
                <p>Get an API key from your OpenAI dashboard. <a href="https://platform.openai.com/api-keys" target="_blank" class="text-blue-400 hover:underline">Get an API key here.</a></p>`;
        } else if (p === 'anthropic') {
            aiInstructions.innerHTML = `<h4 class="font-bold text-emerald-400 mb-2"><i class="fa-solid fa-circle-info"></i> How to connect Anthropic</h4>
                <p>Get an API key from Anthropic Console. <a href="https://console.anthropic.com/settings/keys" target="_blank" class="text-blue-400 hover:underline">Get an API key here.</a></p>`;
        }
    };

    if (aiProviderSelect) {
        updateAiInstructions();
        aiProviderSelect.addEventListener('change', updateAiInstructions);
    }

    if (aiSettingsForm) {
        aiSettingsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const provider = aiProviderSelect.value;
            const token = aiTokenInput.value.trim();

            if (!provider) return;

            const originalText = aiSubmitBtn.innerHTML;
            aiSubmitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';
            aiSubmitBtn.disabled = true;
            aiStatusMessage.classList.add('hidden');

            const payload = {
                ai_provider: provider,
                ai_token: token || "UNCHANGED"
            };

            try {
                const response = await fetch('/api/users/me', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (response.ok) {
                    aiStatusMessage.textContent = 'AI Settings Updated Successfully!';
                    aiStatusMessage.className = 'text-sm rounded p-3 text-center font-bold bg-green-500/20 text-green-400 border border-green-500/30';
                    aiStatusMessage.classList.remove('hidden');
                    aiTokenInput.placeholder = "•••••••••••••••• (Saved)";
                    aiTokenInput.value = "";
                } else {
                    const err = await response.json();
                    aiStatusMessage.textContent = `Update Failed: ${err.detail || 'Error'}`;
                    aiStatusMessage.className = 'text-sm rounded p-3 text-center font-bold bg-red-500/20 text-red-400 border border-red-500/30';
                    aiStatusMessage.classList.remove('hidden');
                }
            } catch (error) {
                aiStatusMessage.textContent = 'Network error.';
                aiStatusMessage.className = 'text-sm rounded p-3 text-center font-bold bg-red-500/20 text-red-400 border border-red-500/30';
                aiStatusMessage.classList.remove('hidden');
            } finally {
                aiSubmitBtn.innerHTML = originalText;
                aiSubmitBtn.disabled = false;
            }
        });
    }

    // Dev Logs Logic
    const logTypeFilter = document.getElementById('log-type-filter');
    const logSearchInput = document.getElementById('log-search-input');
    const refreshLogsBtn = document.getElementById('refresh-logs-btn');
    const logViewer = document.getElementById('log-viewer');
    const logCount = document.getElementById('log-count');
    
    let rawLogs = [];

    const fetchLogs = async () => {
        logViewer.innerHTML = '<div class="text-center text-gray-500 py-10"><i class="fa-solid fa-spinner fa-spin mr-2"></i>Loading logs...</div>';
        try {
            const res = await fetch('/api/logs');
            const data = await res.json();
            rawLogs = data.logs || [];
            renderLogs();
        } catch (e) {
            logViewer.innerHTML = '<div class="text-center text-red-500 py-10">Failed to load logs.</div>';
        }
    };

    const renderLogs = () => {
        const type = logTypeFilter.value;
        const query = logSearchInput.value.toLowerCase();
        
        let filtered = rawLogs.filter(line => {
            if (type !== 'ALL' && !line.includes(`[${type}]`)) return false;
            if (query && !line.toLowerCase().includes(query)) return false;
            return true;
        });

        logCount.textContent = `${filtered.length} lines`;
        logViewer.innerHTML = '';
        
        if (filtered.length === 0) {
            logViewer.innerHTML = '<div class="text-gray-500 p-2 text-center mt-4">No logs match the current filters.</div>';
            return;
        }

        filtered.forEach(line => {
            const div = document.createElement('div');
            let className = 'text-gray-300 hover:bg-[#2B2D31] px-1 rounded';
            if (line.includes('[ERROR]')) className = 'text-red-400 font-bold hover:bg-[#2B2D31] px-1 rounded';
            else if (line.includes('[WARNING]')) className = 'text-yellow-400 hover:bg-[#2B2D31] px-1 rounded';
            else if (line.includes('[INFO]')) className = 'text-blue-300 hover:bg-[#2B2D31] px-1 rounded';
            
            div.className = className;
            div.textContent = line;
            logViewer.appendChild(div);
        });

        logViewer.scrollTop = logViewer.scrollHeight;
    };

    if (logTypeFilter) logTypeFilter.addEventListener('change', renderLogs);
    if (logSearchInput) logSearchInput.addEventListener('input', renderLogs);
    if (refreshLogsBtn) refreshLogsBtn.addEventListener('click', fetchLogs);

    
// --- 5. PLATFORM SETUP MODAL ---
    const platformSelect = document.getElementById('platform-select');
    const platformInstructions = document.getElementById('platform-instructions');
    const fieldCustomNameContainer = document.getElementById('field-custom-name-container');
    const fieldAccountIdContainer = document.getElementById('field-account-id-container');
    const fieldTokenContainer = document.getElementById('field-token-container');
    const labelAccountId = document.getElementById('label-account-id');
    const labelToken = document.getElementById('label-token');
    const inputCustomName = document.getElementById('platform-custom-name');
    const inputAccountId = document.getElementById('platform-account-id');
    const inputToken = document.getElementById('platform-token');
    const submitBtn = document.getElementById('platform-submit-btn');
    const closeSuccessBtn = document.getElementById('platform-close-success-btn');
    const statusMessage = document.getElementById('platform-status-message');

    if (addPlatformBtn) {
        addPlatformBtn.addEventListener('click', () => {
            platformModal.classList.remove('hidden');
            platformModal.classList.add('flex');
            
            // Reset form state
            platformForm.reset();
            document.getElementById("platform-modal-title").textContent = "Connect Platform";
            document.getElementById("edit-platform-id").value = "";
            platformSelect.disabled = false;
            document.getElementById("discord-channels-container").classList.add("hidden");
            submitBtn.textContent = "Connect Platform";

            platformSelect.value = "";
            inputCustomName.value = "";
            platformInstructions.classList.add('hidden');
            fieldCustomNameContainer.classList.add('hidden');
            fieldAccountIdContainer.classList.add('hidden');
            fieldTokenContainer.classList.add('hidden');
            statusMessage.classList.add('hidden');
            submitBtn.classList.remove('hidden');
            submitBtn.disabled = true;
            closeSuccessBtn.classList.add('hidden');
        });
    }

    if (closePlatformModal) {
        closePlatformModal.addEventListener('click', () => {
            platformModal.classList.add('hidden');
            platformModal.classList.remove('flex');
        });
    }

    if (closeSuccessBtn) {
        closeSuccessBtn.addEventListener('click', () => {
            window.location.reload();
        });
    }

    const validatePlatformForm = () => {
        const platform = platformSelect.value;
        if (!platform) {
            submitBtn.disabled = true;
            return;
        }

        let isValid = true;
        const editId = document.getElementById("edit-platform-id").value;
        if (!editId) {
            if (!fieldCustomNameContainer.classList.contains('hidden') && !inputCustomName.value.trim()) isValid = false;
            if (!fieldAccountIdContainer.classList.contains('hidden') && !inputAccountId.value.trim()) isValid = false;
            if (!fieldTokenContainer.classList.contains('hidden') && !inputToken.value.trim()) isValid = false;
        }

        submitBtn.disabled = !isValid;
    };

    if (platformSelect) {
        platformSelect.addEventListener('change', () => {
            const platform = platformSelect.value;
            statusMessage.classList.add('hidden');
            
            inputCustomName.value = '';
            inputAccountId.value = '';
            inputToken.value = '';

            platformInstructions.classList.remove('hidden');
            fieldCustomNameContainer.classList.remove('hidden');
            fieldAccountIdContainer.classList.remove('hidden');
            fieldTokenContainer.classList.remove('hidden');

            if (platform === 'DISCORD') {
                platformInstructions.innerHTML = `<i class="fa-solid fa-circle-info text-emerald-500"></i> Create an app in the Discord Developer Portal, add a Bot, and invite it to your server with 'Read Message History' & 'Send Messages' permissions.`;
                labelAccountId.textContent = 'Server ID';
                inputAccountId.placeholder = 'e.g. 123456789012345678';
                labelToken.textContent = 'Bot Token';
                inputToken.placeholder = 'MTI...';
            } else if (platform === 'INSTAGRAM' || platform === 'FACEBOOK') {
                platformInstructions.innerHTML = `<i class="fa-solid fa-circle-info text-pink-500"></i> You must have a Meta Business Account. <a href="https://www.facebook.com/business/help/502981923235522" target="_blank" class="text-emerald-400 hover:underline">View Docs</a>`;
                labelAccountId.textContent = 'Page / Account ID';
                inputAccountId.placeholder = 'e.g. 123456789';
                labelToken.textContent = 'User Access Token';
                inputToken.placeholder = 'EAA...';
            } else if (platform === 'TIKTOK') {
                platformInstructions.innerHTML = `<i class="fa-solid fa-circle-info text-white"></i> You must have a TikTok Business Account. <a href="https://ads.tiktok.com/help/article/getting-started-tiktok-for-business" target="_blank" class="text-emerald-400 hover:underline">View Docs</a>`;
                labelAccountId.textContent = 'Account ID';
                inputAccountId.placeholder = 'e.g. 987654321';
                labelToken.textContent = 'Access Token';
                inputToken.placeholder = 'Enter TikTok Token...';
            } else if (platform === 'YOUTUBE') {
                platformInstructions.innerHTML = `<i class="fa-solid fa-circle-info text-red-500"></i> Provide your YouTube Channel ID and OAuth Token.`;
                labelAccountId.textContent = 'Channel ID';
                inputAccountId.placeholder = 'UC...';
                labelToken.textContent = 'OAuth Access Token';
                inputToken.placeholder = 'ya29...';
            }

            validatePlatformForm();
        });
    }

    inputCustomName.addEventListener('input', validatePlatformForm);
    inputAccountId.addEventListener('input', validatePlatformForm);
    inputToken.addEventListener('input', validatePlatformForm);

    if (platformForm) {
        platformForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Testing Connection...';
            submitBtn.disabled = true;
            statusMessage.classList.add('hidden');

            const platform_name = platformSelect.value;
            const custom_name = inputCustomName.value.trim();
            const account_id = inputAccountId.value.trim();
            const token = inputToken.value.trim();

            try {
                const editId = document.getElementById("edit-platform-id").value;
            const url = editId ? `/api/platforms/${editId}` : '/api/platforms';
            const method = editId ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    platform_name, 
                    custom_name: custom_name || "UNCHANGED", 
                    account_id: account_id || "UNCHANGED", 
                    token: token || "UNCHANGED",
                    selected_channels: platform_name === 'DISCORD' ? 
                        Array.from(document.querySelectorAll('.discord-channel-checkbox:checked')).map(cb => cb.value) : 
                        null
                })
            });

                if (response.ok) {
                    statusMessage.textContent = 'Connection Successful!';
                    statusMessage.className = 'text-sm rounded p-3 text-center font-bold bg-green-500/20 text-green-400 border border-green-500/30';
                    statusMessage.classList.remove('hidden');
                    
                    submitBtn.classList.add('hidden');
                    closeSuccessBtn.classList.remove('hidden');
                } else {
                    const err = await response.json();
                    statusMessage.textContent = `Connection Failed: ${err.detail || 'Invalid Credentials'}`;
                    statusMessage.className = 'text-sm rounded p-3 text-center font-bold bg-red-500/20 text-red-400 border border-red-500/30';
                    statusMessage.classList.remove('hidden');
                    submitBtn.innerHTML = originalText;
                }
            } catch (error) {
                statusMessage.textContent = 'Network error. Could not connect platform.';
                statusMessage.className = 'text-sm rounded p-3 text-center font-bold bg-red-500/20 text-red-400 border border-red-500/30';
                statusMessage.classList.remove('hidden');
                submitBtn.innerHTML = originalText;
            }
        });
    }

    
    const loadingOverlay = document.getElementById("loading-overlay");
    const loadingText = document.getElementById("loading-text");

    document.querySelectorAll(".refresh-btn").forEach(btn => {
        btn.addEventListener("click", async (e) => {
            e.stopPropagation(); // prevent tab select
            const platform = e.target.dataset.platform;
            
            loadingOverlay.classList.remove("hidden");
            loadingOverlay.classList.add("flex");
            mainApp.classList.add("blur-sm");
            
            if (platform === "All Messages" || platform === "ALL") {
                loadingText.textContent = "Gathering messages from all platforms...";
            } else {
                loadingText.textContent = `Gathering messages from ${platform}...`;
            }

            // Trigger backend sync process
            try {
                const url = `/api/messages/sync${platform !== 'All Messages' && platform !== 'ALL' ? '?platform=' + platform : ''}`;
                await fetch(url, { method: 'POST' });
                // Actually fetch them from the updated database
                await fetchMessages(currentFilter);
            } finally {
                loadingOverlay.classList.add("hidden");
                loadingOverlay.classList.remove("flex");
                mainApp.classList.remove("blur-sm");
            }
        });
    });

    // Handle Edit gear clicks
    document.querySelectorAll(".edit-platform-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            e.stopPropagation();
            const id = e.target.dataset.id;
            const platformName = e.target.dataset.platform;
            const accountId = e.target.dataset.account;
            const customName = e.target.dataset.customName;
            
            document.getElementById("platform-modal-title").textContent = "Edit Platform";
            document.getElementById("edit-platform-id").value = id;
            
            platformModal.classList.remove("hidden");
            platformModal.classList.add("flex");
            
            platformSelect.value = platformName;
            platformSelect.disabled = true; // Cannot edit platform type
            platformSelect.dispatchEvent(new Event("change"));
            
            inputCustomName.value = "";
            inputCustomName.placeholder = `Current: ${customName || "None"}`;
            inputAccountId.value = "";
            inputAccountId.placeholder = `Current: ${accountId || "None"}`;
            inputToken.value = ""; // Don't show old token
            inputToken.placeholder = "Enter new token (optional)";
            
            // Handle Discord Channels Checklist
            const channelsContainer = document.getElementById("discord-channels-container");
            const channelsList = document.getElementById("discord-channels-list");
            channelsContainer.classList.add("hidden");
            
            if (platformName === "DISCORD") {
                channelsContainer.classList.remove("hidden");
                channelsList.innerHTML = `<div class="text-center text-gray-500 py-2"><i class="fa-solid fa-spinner fa-spin"></i> Loading channels...</div>`;
                
                fetch(`/api/platforms/${id}/discord_channels`)
                    .then(res => res.json())
                    .then(data => {
                        if (data.detail) {
                            channelsList.innerHTML = `<div class="text-red-400 text-xs py-2">${data.detail}</div>`;
                            return;
                        }
                        
                        channelsList.innerHTML = "";
                        if (data.channels.length === 0) {
                            channelsList.innerHTML = `<div class="text-gray-500 text-xs py-2">No channels found. Verify permissions.</div>`;
                            return;
                        }
                        
                        data.channels.forEach(ch => {
                            const isChecked = data.selected_channels.includes(ch.id) ? "checked" : "";
                            channelsList.innerHTML += `
                                <label class="flex items-center space-x-2 cursor-pointer hover:bg-[#2B2D31] p-1 rounded">
                                    <input type="checkbox" value="${ch.id}" class="discord-channel-checkbox form-checkbox h-4 w-4 text-emerald-500 rounded border-gray-700 bg-gray-900 focus:ring-emerald-500 focus:ring-offset-gray-900" ${isChecked}>
                                    <span class="truncate">#${ch.name}</span>
                                </label>
                            `;
                        });
                    })
                    .catch(err => {
                        channelsList.innerHTML = `<div class="text-red-400 text-xs py-2">Failed to load channels.</div>`;
                    });
            }
            
            submitBtn.disabled = false;
            submitBtn.textContent = "Save Changes";
            submitBtn.classList.remove("hidden");
            closeSuccessBtn.classList.add("hidden");
            statusMessage.classList.add("hidden");
        });
    });

    // Initialize
    const allMsgsRefreshBtn = document.querySelector(".refresh-btn[data-platform=\"All Messages\"]");
    if (allMsgsRefreshBtn && localStorage.getItem("isLocked") !== "true") {
        // Trigger the automatic sync when page loads
        allMsgsRefreshBtn.click();
    } else {
        fetchMessages();
    }
});
