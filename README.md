# فیلترادیوم | Filteradium
## Smart Stock Filtering Platform for Tehran Stock Exchange

### 🎯 Overview

Filteradium is a professional stock filtering and analysis platform for the Tehran Stock Exchange (TSETMC). It provides real-time market data, technical analysis indicators, and advanced filtering capabilities.

### 📥 Download

| Platform | File | Size | Download |
|----------|------|------|----------|
| 🪟 **Windows** | `Filteradium-1.0.0-Windows.exe` | 66.4 MB | [Download](https://github.com/johncrazoova/filteradium/releases/download/v1.0.0/Filteradium-1.0.0-Windows.exe) |
| 🍎 **macOS** | Coming soon | - | Coming soon |
| 🐧 **Linux** | `Filteradium-1.0.0-Linux.AppImage` | 99.5 MB | [Download](https://github.com/johncrazoova/filteradium/releases/download/v1.0.0/Filteradium-1.0.0-Linux.AppImage) |
| 📱 **Android** | `Filteradium-1.0.0-Android.apk` | 22 KB | [Download](https://github.com/johncrazoova/filteradium/releases/download/v1.0.0/Filteradium-1.0.0-Android.apk) |
| 🌐 **Web** | Online App | - | [Launch](#quick-start) |

### 📦 Project Structure

```
filteradium/
├── backend/                    # Python FastAPI backend
│   ├── api/                    # TSETMC API clients
│   ├── core/                   # Indicators, scoring, backtest
│   ├── models/                 # Database models
│   ├── services/               # Market data services
│   └── main.py                 # FastAPI server
├── android/                    # Android app (WebView)
├── desktop/                    # Electron app (Windows/Mac/Linux)
├── styles/                     # CSS styles
├── lib/                        # JavaScript filters
├── index.html                  # Web interface
└── run.py                      # Server launcher
```

### 🚀 Quick Start

#### 1. Backend Server

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run server
python run.py
```

#### 2. Web Interface

Open `index.html` in your browser or access via server.

#### 3. Android App

Download APK from [Releases](https://github.com/johncrazoova/filteradium/releases) and install on your device.

#### 4. Desktop App (Windows/Mac/Linux)

```bash
cd desktop
npm install
npm start
```

To build for your platform:
```bash
npm run build:win    # Windows
npm run build:mac    # macOS
npm run build:linux  # Linux
```

### 📊 Features

- **Real-time Market Data**: Live prices and market watch
- **Technical Indicators**: 30+ indicators (RSI, MACD, Bollinger, etc.)
- **Smart Scoring**: Multi-factor scoring engine
- **Backtesting**: Test strategies on historical data
- **Custom Filters**: Create and save your own filters
- **User Profiles**: Personalized dashboard
- **Cross-platform**: Works on all devices

### 🔧 Technical Stack

| Component | Technology |
|-----------|------------|
| Backend | Python FastAPI |
| Database | SQLAlchemy + SQLite |
| Frontend | HTML/CSS/JavaScript |
| Android | WebView |
| Desktop | Electron |
| Indicators | NumPy/Pandas |

### 📝 License

MIT License

### 🤝 Contributing

Contributions welcome! Please open an issue or submit a pull request.

### 📧 Contact

- GitHub: [@johncrazoova](https://github.com/johncrazoova)
