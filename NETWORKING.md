# Networking Guide

## Default Configuration

Ollama Shim binds to `0.0.0.0:11434` (all interfaces, Ollama's standard port).

## Common Scenarios

### 1. Everything on One Machine (Simplest)
```
Backend (localhost:1234) → Ollama Shim (localhost:11434) → Client app
```

**.env:**
```ini
BACKEND_BASE_URL=http://localhost:1234
SHIM_PORT=11434
```

### 2. LM Studio on Different Machine
```
Backend (192.168.1.10:1234) → Ollama Shim (this machine:11434) → Clients
```

**.env:**
```ini
BACKEND_BASE_URL=http://192.168.1.10:1234
SHIM_PORT=11434
```

### 3. Shim on Server, Accessed Remotely
```
Backend (server:1234) → Ollama Shim (server:11434) ← Client (anywhere)
```

Clients connect to: `http://server-ip:11434`

## WSL2 Networking

### Default WSL2 (NAT Mode)

- WSL2 gets private IP (e.g., `172.19.x.x`)
- Windows auto-forwards `localhost` → WSL2
- From Windows: `http://localhost:11434` works
- From other machines: Won't work without port forwarding

**Enable external access:**
```powershell
# Windows (as Admin) - get WSL2 IP with: wsl hostname -I
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=11434 connectaddress=172.19.x.x connectport=11434
```

### WSL2 Mirrored Mode (Recommended)

Newer WSL2 supports network bridging. Add to `C:\Users\YourName\.wslconfig`:

```ini
[wsl2]
networkingMode=mirrored
```

Restart WSL2:
```powershell
wsl --shutdown
wsl
```

Now WSL2 shares Windows network interfaces directly - no port forwarding needed.

## Checking Network Status

**Linux:**
```bash
# See what's listening
ss -tlnp | grep 11434

# Check your IPs
ip addr show

# Test locally
curl http://localhost:11434/api/tags
```

**Windows:**
```powershell
# See what's listening
netstat -an | findstr 11434

# Check your IPs
ipconfig

# Test locally
curl http://localhost:11434/api/tags
```

## Troubleshooting

**"Connection refused"**
1. Is the service running? (`systemctl status ollama-shim` or `net start OllamaShim`)
2. Check firewall rules
3. Verify port: `ss -tlnp | grep 11434` (Linux) or `netstat -an | findstr 11434` (Windows)

**"Can't reach from another machine"**
1. Firewall blocking? (see INSTALL.md)
2. WSL2 NAT mode? (see above)
3. Binding to `127.0.0.1` instead of `0.0.0.0`? (check uvicorn args)

**"Can't reach backend"**
1. Is backend running? Test: `curl http://localhost:1234/v1/models`
2. Check `BACKEND_BASE_URL` in `.env`
3. If backend is on different machine, use its IP not `localhost`