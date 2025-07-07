# discovery

The `discovery` module handles peer announcement and discovery across the LAN using UDP multicast.

## Features
- `Announcer`: broadcast node presence
- `Listener`: listen for peer announcements
- Simple binary protocol for low-latency payloads

## Getting Started
1. Install dependencies: `pip install -r requirements.txt`
2. Run the announcer: see `announcer.py` usage
3. Run the listener: see `listener.py` usage
4. Optional: specify `interface_ip` to bind a specific NIC
5. Register `on_removed` or `on_timeout` callbacks to track peer departure

## Running Discovery

```bash
# In one terminal, start listener:
python -c "from discovery.listener import Listener; import asyncio; \
 listener = Listener(lambda nid, ip, port, ts: print(f'Found: {ip}:{port}')); \
 asyncio.run(listener.start())"

# In another, start announcer:
python -c "from discovery.announcer import Announcer; import uuid, asyncio; \
node_id = uuid.uuid4().bytes; announcer = Announcer(node_id, port=5001); \
asyncio.run(announcer.start())"
```

Call ``stop()`` on either class to shut down gracefully.
