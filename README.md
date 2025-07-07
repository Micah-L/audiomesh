AudioMesh

AudioMesh is a lightweight, LAN-based audio distribution framework for Linux devices. It allows you to share audio inputs and outputs across multiple machines and control routing through a simple web-based UI.

## Features

- **Multi-node audio sharing**: Broadcast or collect audio streams between Linux devices over the local network.
- **Input/output routing**: Map any machine's audio input or output device to any node in the mesh.
- **Web UI**: Lightweight HTTP server with a dashboard to view available nodes and configure routing.
- **Low latency**: Uses efficient audio streaming protocols to minimize delay.
- **Modular design**: Easily extendable with custom audio drivers or network backends.

## Requirements

- Linux-based OS on each node.
- Python 3.8+ or C++17 toolchain (depending on chosen implementation).
- ALSA (for audio capture/playback) or PulseAudio/Jack support.
- `pip` (if using the Python package) or `cmake` and `make`.
- Web browser for accessing the UI.

## Installation

### Python version

```bash
# Clone the repo
$ git clone https://github.com/your-org/audiomesh.git
$ cd audiomesh

# Install dependencies
$ pip install -r requirements.txt

# Optional: install as package
$ pip install .
```

### C++ version

```bash
# Clone and build
$ git clone https://github.com/your-org/audiomesh.git
$ cd audiomesh
$ mkdir build && cd build
$ cmake ..
$ make
$ sudo make install
```

## Configuration

All configuration is managed via `config.yaml` in the project root:

```yaml
# Example config.yaml
node_name: node01
listen_port: 5000
backend: alsa            # or pulse, jack
ui_port: 8080
nodes:
  - host: node02.local
    port: 5000
  - host: node03.local
    port: 5000
```

- `node_name`: Unique identifier for this node.
- `listen_port`: Port for audio mesh communication.
- `backend`: Audio subsystem (`alsa`, `pulse`, `jack`).
- `ui_port`: HTTP port for the Web UI.
- `nodes`: List of peer nodes in the mesh.

## Usage

Start AudioMesh on each device:

```bash
$ audiomesh --config config.yaml
```

Open your browser to `http://<node_host>:<ui_port>`.

In the dashboard, select source node and device (e.g., microphone, system output).
Select target node(s) and target device(s) (e.g., speakers, recording device).
Click **Apply** to establish the stream.

## Web UI Endpoints

- `/` - Dashboard overview.
- `/api/nodes` - `GET` list of discovered nodes.
- `/api/routes` - `GET`/`POST` current routing table.
- `/api/devices` - `GET` list of local audio devices.

## Development

- **Code style**: Follow PEP8 (Python) or Google C++ style guide.
- **Testing**: Unit tests under `tests/`; use `pytest` (Python) or `ctest` (C++).
- **Linting**: `flake8` and `clang-format`.

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feat/your-feature`.
3. Commit changes and push to your branch.
4. Open a Pull Request describing your changes.

## License

MIT License. See `LICENSE` for details.

