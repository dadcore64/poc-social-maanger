import sqlite3

# 1. DB Migration
for db_name in ["socialease.db", "test.db"]:
    try:
        db = sqlite3.connect(db_name)
        db.execute("ALTER TABLE incoming_messages ADD COLUMN channel_name VARCHAR(255)")
        db.commit()
        db.close()
    except Exception:
        pass

# 2. Update Models
with open("app/models.py", "r", encoding="utf-8") as f:
    models = f.read()
if "channel_name: Mapped[" not in models:
    models = models.replace(
        "timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)",
        "timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)\n    channel_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)"
    )
    with open("app/models.py", "w", encoding="utf-8") as f:
        f.write(models)

# 3. Update Dashboard
with open("app/templates/dashboard.html", "r", encoding="utf-8") as f:
    html = f.read()
html = html.replace(
    """<h2 class="text-xl font-bold text-white mb-2">Welcome Back!</h2>""",
    """<h2 class="text-xl font-bold text-white mb-2">Alright Then, Keep Your Secrets.</h2>"""
)
with open("app/templates/dashboard.html", "w", encoding="utf-8") as f:
    f.write(html)

# 4. Update messages.py
with open("app/routers/messages.py", "r", encoding="utf-8") as f:
    msg_py = f.read()

if "channel_name" not in msg_py:
    msg_py = msg_py.replace(
        """"platform_custom_name": msg.platform.custom_name if msg.platform else None,
            "sender_name": msg.sender_name,""",
        """"platform_custom_name": msg.platform.custom_name if msg.platform else None,
            "sender_name": msg.sender_name,
            "channel_name": msg.channel_name,"""
    )
    
    old_loop = """for channel_id in selected_channels:
                    base_url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=100"
                    headers = {"Authorization": f"Bot {access_token}"}
                    
                    try:
                        last_msg_id = None"""
    new_loop = """for channel_id in selected_channels:
                    base_url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=100"
                    headers = {"Authorization": f"Bot {access_token}"}
                    
                    # Fetch channel name
                    channel_name = "unknown"
                    try:
                        ch_resp = await client.get(f"https://discord.com/api/v10/channels/{channel_id}", headers=headers)
                        if ch_resp.status_code == 200:
                            channel_name = ch_resp.json().get("name", "unknown")
                    except Exception:
                        pass
                        
                    try:
                        last_msg_id = None"""
    msg_py = msg_py.replace(old_loop, new_loop)
    
    old_create = """new_msg = IncomingMessage(
                                        connection_id=conn.id,
                                        external_message_id=ext_id,
                                        sender_name=sender,
                                        sender_avatar_url=avatar_url,
                                        content=content,
                                        timestamp=ts
                                    )"""
    new_create = """new_msg = IncomingMessage(
                                        connection_id=conn.id,
                                        external_message_id=ext_id,
                                        sender_name=sender,
                                        sender_avatar_url=avatar_url,
                                        content=content,
                                        timestamp=ts,
                                        channel_name=channel_name
                                    )"""
    msg_py = msg_py.replace(old_create, new_create)
    
    with open("app/routers/messages.py", "w", encoding="utf-8") as f:
        f.write(msg_py)

# 5. Update app.js
with open("app/static/js/app.js", "r", encoding="utf-8") as f:
    js = f.read()

old_html = """<span class="text-[10px] uppercase bg-gray-800 px-1.5 py-0.5 rounded text-gray-400">${msg.platform_custom_name || msg.platform}</span>
                        <span class="text-xs text-gray-400">${timeString}</span>"""
new_html = """<span class="text-[10px] uppercase bg-gray-800 px-1.5 py-0.5 rounded text-gray-400">${msg.platform_custom_name || msg.platform}</span>
                        ${msg.platform === 'DISCORD' && msg.channel_name && msg.channel_name !== 'unknown' ? `<span class="text-[10px] uppercase bg-[#5865F2]/20 text-[#5865F2] px-1.5 py-0.5 rounded">#${msg.channel_name}</span>` : ''}
                        <span class="text-xs text-gray-400">${timeString}</span>"""

if "msg.channel_name" not in js:
    js = js.replace(old_html, new_html)
    with open("app/static/js/app.js", "w", encoding="utf-8") as f:
        f.write(js)

print("Tweak complete")
