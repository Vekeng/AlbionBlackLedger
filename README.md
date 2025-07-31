# 🧾 Albion Online Black Ledger

## 📚 Table of Contents

- 🧾 [Albion Online Black Ledger](#-albion-online-black-ledger)
- ⚙️ [Requirements](#️-requirements)
- ✨ [Features](#-features)
- 📥 [Albion Data Client](#-albion-data-client)
  - [On Windows](#on-windows)
  - [On Linux](#on-linux)
- 💡 [How to use Black Ledger](#-how-to-use-black-ledger)

---

**Albion Online Black Ledger** is a local desktop application that helps you track your market flips and evaluate Black Market trading opportunities in **Albion Online**.

It listens to live market data sent from the [Albion Data Client](https://github.com/ao-data/albiondata-client) and stores it locally in an SQLite database for filtering, sorting, and future analysis — all within a clean graphical interface.

---

## ⚙️ Requirements

- [Albion Data Client](https://github.com/ao-data/albiondata-client/releases) (must be running and properly configured)
- Albion Online game client (logged in)

---

## ✨ Features

- 🔄 Real-Time Market Logging – Instantly captures data as you browse the in-game market
- 💾 Local-Only Storage – All data is saved on your machine; no uploads, no sharing
- 🪄 Supports Flips with enchantments – buy, enchant, sell for even more profit

---

## 📥 Albion Data Client

1. **Download the latest release from:**

   👉 [https://github.com/ao-data/albiondata-client/releases](https://github.com/ao-data/albiondata-client/releases)

2. **Install the client**

### On Windows
Start the albiondata-client.exe with `-i http://localhost:5000`: 
3. **Open Command Prompt or PowerShell**  
   - Press `Win + R`, type `cmd` or `powershell`, then press Enter.

4. **Navigate to the installation folder**  

   ```powershell
   cd "C:\Program Files\Albion Data Client"

5. **Run the client with the local server URL**

   .\albiondata-client.exe -i http://localhost:5000

### On Linux
If you are on Linux, you should now what to do. 

---

## 💡 How to use Black Ledger

1. **With Albion Data Client running, scan the market where you buy items and Black Market** - go to market in game and start browsing items for potential flips. 

2. **Set "From" field in Black Ledger to market where you buy items**

3. **Optionally scan prices of the echantment materials: runes, souls, relics. Press "Get Prices" button in Black Ledger to set the prices**

4. **Press "Find Flips!"** - you will see possible flips in Black Ledger. If there are possible enchantment flips - you will see the costs of enchantments. 

5. **After you finish flipping session, press "Clear Data"**
