# Quick Test Script for User Prompt Debugging

## Issue: User prompt dialog not appearing after Nmap scan

### Debugging Steps:

1. **Check Backend is Running**
   ```powershell
   # In terminal, check if backend is running on port 8000
   Test-NetConnection -ComputerName localhost -Port 8000
   ```

2. **Restart Backend with Debug Output**
   ```powershell
   cd c:\Users\cisco\Documents\Niru-Predictpath-AI\NiRu-predictpath-tools\predictpath-ui\backend
   python main.py
   ```
   
   Look for debug messages:
   - `[DEBUG] Sending user prompt to WebSocket...`
   - `[DEBUG] User prompt sent successfully`

3. **Check Browser Console**
   - Open browser DevTools (F12)
   - Go to Console tab
   - Run scan again
   - Look for debug messages:
     - `[DEBUG] Parsed JSON message: {type: 'user_prompt', ...}`
     - `[DEBUG] User prompt detected! Showing dialog...`

4. **Check WebSocket Connection**
   - In browser DevTools → Network tab
   - Filter by "WS" (WebSocket)
   - Click on `/ws/scan` connection
   - Check "Messages" tab to see what's being sent/received

### Common Issues:

**Issue 1: Backend not running**
- Solution: Restart backend with `python main.py`

**Issue 2: Old backend code running**
- Solution: Stop backend (Ctrl+C), restart

**Issue 3: Browser cache**
- Solution: Hard refresh (Ctrl+Shift+R) or clear cache

**Issue 4: WebSocket not connecting**
- Check console for "WebSocket Error: Failed to connect to scanner backend"
- Verify backend is on port 8000

### File Cleanup for Fresh Run:

You can now delete scan logs using the Reset function:

```powershell
# Manual cleanup
Remove-Item "c:\Users\cisco\Documents\Niru-Predictpath-AI\NiRu-predictpath-tools\logs\nmap\*" -Force
Remove-Item "c:\Users\cisco\Documents\Niru-Predictpath-AI\NiRu-predictpath-tools\logs\openvas\*" -Force
```

Or use the UI Reset button (Soft Reset will clear scan logs).

### Test the Prompt Manually:

If you want to test just the prompt without running Nmap:

1. Open browser console
2. Paste this code:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/scan');
ws.onopen = () => {
    console.log('WebSocket connected');
    ws.send(JSON.stringify({scan_type: 'network'}));
};
ws.onmessage = (event) => {
    console.log('Received:', event.data);
    try {
        const json = JSON.parse(event.data);
        console.log('Parsed JSON:', json);
    } catch (e) {
        console.log('Text message:', event.data);
    }
};
```

This will show you exactly what messages are being received.
