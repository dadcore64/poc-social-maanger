import sqlite3
import re

# 1. Update DB schema
db = sqlite3.connect("socialease.db")
try:
    db.execute("ALTER TABLE platform_connections ADD COLUMN custom_name VARCHAR(255)")
    db.execute("UPDATE platform_connections SET custom_name = account_id WHERE custom_name IS NULL")
    db.commit()
except Exception as e:
    pass
db.close()

# 2. Update models.py
with open("app/models.py", "r", encoding="utf-8") as f:
    models = f.read()

if "custom_name: Mapped[" not in models:
    models = models.replace(
        "encrypted_token: Mapped[str] = mapped_column(String(500))",
        "encrypted_token: Mapped[str] = mapped_column(String(500))\n    custom_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)"
    )
    with open("app/models.py", "w", encoding="utf-8") as f:
        f.write(models)

# 3. Update platforms.py
with open("app/routers/platforms.py", "r", encoding="utf-8") as f:
    routers = f.read()

if "custom_name: str" not in routers:
    routers = routers.replace(
        "class PlatformCreate(BaseModel):\n    platform_name: str\n    account_id: str\n    token: str",
        "class PlatformCreate(BaseModel):\n    platform_name: str\n    custom_name: str\n    account_id: str\n    token: str"
    )
    routers = routers.replace(
        "class PlatformUpdate(BaseModel):\n    platform_name: str\n    account_id: str\n    token: str",
        "class PlatformUpdate(BaseModel):\n    platform_name: str\n    custom_name: str\n    account_id: str\n    token: str"
    )
    routers = routers.replace(
        "account_id=platform_data.account_id,",
        "account_id=platform_data.account_id,\n        custom_name=platform_data.custom_name,"
    )
    routers = routers.replace(
        "conn.account_id = platform_data.account_id",
        "conn.account_id = platform_data.account_id\n    conn.custom_name = platform_data.custom_name"
    )
    with open("app/routers/platforms.py", "w", encoding="utf-8") as f:
        f.write(routers)

# 4. Update dashboard.html
with open("app/templates/dashboard.html", "r", encoding="utf-8") as f:
    html = f.read()

html = html.replace(
    """data-account="{{ conn.account_id }}"
                     {% if conn.platform_name == 'INSTAGRAM'""",
    """data-account="{{ conn.account_id }}"
                     data-custom-name="{{ conn.custom_name or conn.account_id }}"
                     {% if conn.platform_name == 'INSTAGRAM'"""
)
html = html.replace(
    """data-title="{{ conn.account_id }}">""",
    """data-title="{{ conn.custom_name or conn.account_id }}">"""
)
html = html.replace(
    """<span class="truncate text-sm flex-1">{{ conn.account_id }}</span>""",
    """<span class="truncate text-sm flex-1">{{ conn.custom_name or conn.account_id }}</span>"""
)
html = html.replace(
    """data-account="{{ conn.account_id }}" title="Edit"></i>""",
    """data-account="{{ conn.account_id }}" data-custom-name="{{ conn.custom_name or conn.account_id }}" title="Edit"></i>"""
)

field_custom_name = """
                <div id="field-custom-name-container" class="hidden">
                    <label id="label-custom-name" class="block text-xs font-bold text-gray-400 uppercase mb-1">Display Name</label>
                    <input type="text" id="platform-custom-name" placeholder="e.g. My Main Server" class="w-full bg-[#1E1F22] text-white p-2 rounded outline-none border border-gray-900 focus:ring-2 focus:ring-emerald-500">
                </div>
                <div id="field-account-id-container" class="hidden">"""
html = html.replace("""<div id="field-account-id-container" class="hidden">""", field_custom_name)

with open("app/templates/dashboard.html", "w", encoding="utf-8") as f:
    f.write(html)

# 5. Update app.js
with open("app/static/js/app.js", "r", encoding="utf-8") as f:
    js = f.read()

js = js.replace(
    "const fieldAccountIdContainer = document.getElementById('field-account-id-container');",
    "const fieldCustomNameContainer = document.getElementById('field-custom-name-container');\n    const fieldAccountIdContainer = document.getElementById('field-account-id-container');"
)
js = js.replace(
    "const inputAccountId = document.getElementById('platform-account-id');",
    "const inputCustomName = document.getElementById('platform-custom-name');\n    const inputAccountId = document.getElementById('platform-account-id');"
)
js = js.replace(
    "platformSelect.value = \"\";\n            platformInstructions.classList.add('hidden');",
    "platformSelect.value = \"\";\n            inputCustomName.value = \"\";\n            platformInstructions.classList.add('hidden');\n            fieldCustomNameContainer.classList.add('hidden');"
)
js = js.replace(
    "if (!fieldAccountIdContainer.classList.contains('hidden') && !inputAccountId.value.trim()) isValid = false;",
    "if (!fieldCustomNameContainer.classList.contains('hidden') && !inputCustomName.value.trim()) isValid = false;\n        if (!fieldAccountIdContainer.classList.contains('hidden') && !inputAccountId.value.trim()) isValid = false;"
)
js = js.replace(
    "inputAccountId.value = '';\n            inputToken.value = '';\n\n            platformInstructions.classList.remove('hidden');\n            fieldAccountIdContainer.classList.remove('hidden');",
    "inputCustomName.value = '';\n            inputAccountId.value = '';\n            inputToken.value = '';\n\n            platformInstructions.classList.remove('hidden');\n            fieldCustomNameContainer.classList.remove('hidden');\n            fieldAccountIdContainer.classList.remove('hidden');"
)
js = js.replace(
    "inputAccountId.addEventListener('input', validatePlatformForm);",
    "inputCustomName.addEventListener('input', validatePlatformForm);\n    inputAccountId.addEventListener('input', validatePlatformForm);"
)
js = js.replace(
    "const account_id = inputAccountId.value.trim();\n            const token = inputToken.value.trim();",
    "const custom_name = inputCustomName.value.trim();\n            const account_id = inputAccountId.value.trim();\n            const token = inputToken.value.trim();"
)
js = js.replace(
    "body: JSON.stringify({ \n                    platform_name, \n                    account_id,",
    "body: JSON.stringify({ \n                    platform_name, \n                    custom_name, \n                    account_id,"
)
js = js.replace(
    "const accountId = e.target.dataset.account;",
    "const accountId = e.target.dataset.account;\n            const customName = e.target.dataset.customName;"
)
js = js.replace(
    "inputAccountId.value = accountId;",
    "inputCustomName.value = customName;\n            inputAccountId.value = accountId;"
)

with open("app/static/js/app.js", "w", encoding="utf-8") as f:
    f.write(js)

# 6. Patch test_main.py
with open("test_main.py", "r", encoding="utf-8") as f:
    tst = f.read()

tst = tst.replace(
    'payload = {"platform_name": "TIKTOK", "account_id": "test_acc", "token": "test_token"}',
    'payload = {"platform_name": "TIKTOK", "custom_name": "My TikTok", "account_id": "test_acc", "token": "test_token"}'
)

with open("test_main.py", "w", encoding="utf-8") as f:
    f.write(tst)

print("Patch complete")
