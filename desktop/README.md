# Filteradium Desktop

Desktop application for Filteradium - Smart Stock Filtering Platform.

## Features

- Works on Windows, macOS, and Linux
- Native look and feel
- Auto-update support
- Offline capable

## Development

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Install Dependencies

```bash
npm install
```

### Run in Development

```bash
npm start
```

### Build for Your Platform

```bash
# Windows
npm run build:win

# macOS
npm run build:mac

# Linux
npm run build:linux

# All platforms
npm run build:all
```

### Output

Built files will be in the `dist/` folder:

- **Windows**: `Filteradium-1.0.0-win.exe` (installer) or `Filteradium-1.0.0-win.exe` (portable)
- **macOS**: `Filteradium-1.0.0-mac.dmg`
- **Linux**: `Filteradium-1.0.0-linux.AppImage`, `.deb`, `.rpm`

## Configuration

Edit `main.js` to change the server URL:

```javascript
const SERVER_URL = 'http://YOUR_SERVER_IP:8000';
```

## License

MIT
