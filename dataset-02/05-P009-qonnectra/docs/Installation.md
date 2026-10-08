## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 22+ (for local frontend development)
- Python 3.12+ (for local backend development)
- uv package manager (optional, recommended for Python)

### Getting Started

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd qonnectra
   ```

2. **Set up environment variables**

   Create a `.env` file in the `deployment/` directory. See [Deployment README](deployment/README.md) for required variables.

3. **Start services with Docker Compose**

   ```bash
   cd deployment
   docker-compose up -d --build
   ```

4. **Access the application**
   - Frontend: `https://app.localhost` (or `http://localhost:5173` for local dev)
   - API: `https://api.localhost` (or `http://localhost:8000` for local dev)
   - Admin: `https://api.localhost/admin`
   - QGIS Server: `https://qgis.localhost/ows/?MAP=/projects/<project>.qgs`
   - TileServer: `https://tiles.localhost`
   - Files (WebDAV): `https://files.localhost`

For detailed setup instructions, see the READMEs in each directory:

- [Backend Setup](backend/README.md)
- [Frontend Setup](frontend/README.md)
- [Deployment Guide](deployment/README.md)
