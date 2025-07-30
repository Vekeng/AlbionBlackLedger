# 🧾 Albion Online Black Ledger

**Albion Online Black Ledger** is a local desktop application that helps you track your market flips and evaluate Black Market trading opportunities in **Albion Online**.

It listens to live market data sent from the [Albion Data Client](https://github.com/ao-data/albiondata-client) and stores it locally in an SQLite database for filtering, sorting, and future analysis — all within a clean graphical interface.

---

## ⚙️ Requirements

- [Albion Data Client](https://github.com/ao-data/albiondata-client/releases) (must be running and properly configured)
- Albion Online game client (logged in)

---

## 📥 Install Albion Data Client

1. Download the latest release from:

   👉 [https://github.com/ao-data/albiondata-client/releases](https://github.com/ao-data/albiondata-client/releases)

2. Extract the archive and run the client **with the correct listener argument**:

   ```bash
   albiondata-client.exe -i http://localhost:5000
