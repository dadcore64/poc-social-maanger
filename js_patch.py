import os

APP_JS_PATH = r"app/static/js/app.js"

with open(APP_JS_PATH, "r", encoding="utf-8") as f:
    js = f.read()

old_edit_js = """            platformSelect.value = platformName;
            platformSelect.disabled = true; // Cannot edit platform type
            platformSelect.dispatchEvent(new Event("change"));
            
            inputAccountId.value = accountId;
            inputToken.value = ""; // Don't show old token
            inputToken.placeholder = "Enter new token (optional)";"""

new_edit_js = """            platformSelect.value = platformName;
            platformSelect.disabled = true; // Cannot edit platform type
            platformSelect.dispatchEvent(new Event("change"));
            
            inputAccountId.value = accountId;
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
            }"""

js = js.replace(old_edit_js, new_edit_js)

old_submit = """body: JSON.stringify({ platform_name, account_id, token: token || "UNCHANGED" }) // token might be unchanged"""
new_submit = """body: JSON.stringify({ 
                    platform_name, 
                    account_id, 
                    token: token || "UNCHANGED",
                    selected_channels: platform_name === 'DISCORD' ? 
                        Array.from(document.querySelectorAll('.discord-channel-checkbox:checked')).map(cb => cb.value) : 
                        null
                })"""

js = js.replace(old_submit, new_submit)

old_add_reset = """            document.getElementById("edit-platform-id").value = "";
            platformSelect.disabled = false;"""
new_add_reset = """            document.getElementById("edit-platform-id").value = "";
            platformSelect.disabled = false;
            document.getElementById("discord-channels-container").classList.add("hidden");"""
js = js.replace(old_add_reset, new_add_reset)

old_discord_instructions = """                labelAccountId.textContent = 'Channel ID';
                inputAccountId.placeholder = 'e.g. 123456789012345678';"""
new_discord_instructions = """                labelAccountId.textContent = 'Server ID';
                inputAccountId.placeholder = 'e.g. 123456789012345678';"""
js = js.replace(old_discord_instructions, new_discord_instructions)

with open(APP_JS_PATH, "w", encoding="utf-8") as f:
    f.write(js)
