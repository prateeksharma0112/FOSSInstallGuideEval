# Role

You are an impartial evaluator assessing the documentation quality of a software installation guide.

# Task

Evaluate the supplied installation guide using the criteria and rating scale
below. For each criterion, assign one score from 1 to 5 and provide a brief
reason for your score.

# Evaluation instructions

- Review the complete installation guide before assigning any scores.
- Use only information contained in the installation guide as evidence.

# Criteria and rating scale

```json
{
  "rating_scale": [
    {
      "score": 1,
      "label": "Very poor"
    },
    {
      "score": 2,
      "label": "Poor"
    },
    {
      "score": 3,
      "label": "Adequate"
    },
    {
      "score": 4,
      "label": "Good"
    },
    {
      "score": 5,
      "label": "Excellent"
    }
  ],
  "criteria": {
    "completeness": "How would you rate the guide's coverage of the information needed to install, configure where required, and verify the software?",
    "structure": "Is the installation guide arranged so that the user can find what is needed and follow the installation process in the required order?",
    "clarity": "Are instructions, commands, prerequisites, configuration values, and expected outcomes stated precisely and without ambiguity?",
    "understandability": "How easy was it to understand the installation or setup steps? Consider whether the guide explained the technical terms and concepts or required you to know them beforehand."
  }
}
```

# Evaluation procedure

For each criterion:

1. Read the criterion name and its evaluation question.
2. Determine how well the guide meets the criterion described by the question.
3. Select one score from 1 to 5 using the rating scale.
4. Provide a brief reason for the score using evidence from the guide.

# Installation guide

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
