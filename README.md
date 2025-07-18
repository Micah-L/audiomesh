# audiomesh

audiomesh is a lightweight, LAN-based audio distribution framework for Linux devices. It allows you to share audio inputs and outputs across multiple machines and control routing through a simple web-based UI.

## Features

- **Multi-node audio sharing**: Broadcast or collect audio streams between Linux devices over the local network.
- **Input/output routing**: Map any machine's audio input or output device to any node in the mesh.
- **Web UI**: Lightweight HTTP server with a dashboard to view available nodes and configure routing.
- **Low latency**: Uses efficient audio streaming protocols to minimize delay.
- **Modular design**: Easily extendable with custom audio drivers or network backends.

## Requirements

- Linux-based OS on each node.
- Python 3.10+
- ALSA (for audio capture/playback) or JACK support.
- `poetry`
- Web browser for accessing the UI.

## Installation

### Setup with Poetry

```bash
# Clone the repo
$ git clone https://github.com/your-org/audiomesh.git
$ cd audiomesh


# Install dependencies
$ poetry install

# Activate the virtual environment
$ poetry shell

# Install git hooks
$ pre-commit install
```

### Install JACK & jacktrip

Run the helper script to install audio prerequisites:

```bash
$ ./scripts/install_prereqs.sh
```

The script is idempotent and works on Ubuntu/Debian or macOS with Homebrew.

### Docker

Build a runtime image with JACK and ``jacktrip`` preinstalled:

```bash
$ docker build -t audiomesh-client -f docker/Dockerfile .
```

Run the container passing your configuration file:

```bash
$ docker run --net=host -v $(pwd)/config.yaml:/app/config.yaml audiomesh-client
```

## Configuration

All configuration is managed via `config.yaml` in the project root:

```yaml
# Example config.yaml
node_name: node01
listen_port: 5000
backend: alsa            # or jack
ui_port: 8080
nodes:
  - host: node02.local
    port: 5000
  - host: node03.local
    port: 5000
```

- `node_name`: Unique identifier for this node.
- `listen_port`: Port for audiomesh communication.
- `backend`: Audio subsystem (`alsa`, `jack`).
- `ui_port`: HTTP port for the Web UI.
- `nodes`: List of peer nodes in the mesh.

## Usage

Start peer discovery on each device:

```bash
$ poetry run discovery start
```

Stop the background discovery daemon:

```bash
$ poetry run discovery stop
```

Start the audio mesh core on each device:

```bash
$ poetry run audiomesh --config config.yaml
```

Start the API server for the dashboard:

```bash
$ poetry run audiomesh api
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

- **Code style**: Follow PEP8.
- **Testing**: Unit tests under `tests/`; run with `poetry run pytest`.
- **Pre-commit hooks**: Run `pre-commit install` after installing dependencies. This
  configures `black`, `isort`, `flake8`, and `mypy` to run automatically before
  each commit.

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feat/your-feature`.
3. Commit changes and push to your branch.
4. Open a Pull Request describing your changes.

## License

MIT License. See `LICENSE` for details.
