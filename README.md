# HackNU Dropouts Backend

AI-powered mockup and content generation API for Figma plugin integration.

## 🚀 Features

- **User Authentication**: JWT-based authentication system
- **Ephemeral File Storage**: Temporary file upload with automatic cleanup (15min TTL)
- **AI Content Generation**: 
  - **Mock Creation**: Generate device mockups, billboard placements, UX showcases
  - **Stock Images**: Brand-safe stock image generation
  - **Stock Videos**: Text-to-video and image-to-video generation
- **Higgsfield AI Integration**: Direct pass-through to Nano Banana, Veo 3, and Kling models

## 📋 Prerequisites

- Python 3.10+
- Higgsfield AI API credentials ([Get them here](https://platform.higgsfield.ai))

## 🛠️ Installation

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd hacknu-back
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your Higgsfield API credentials:

```env
HIGGSFIELD_API_KEY=your-api-key-here
HIGGSFIELD_API_SECRET=your-api-secret-here
SECRET_KEY=change-this-to-random-string-in-production
```

### 4. Run the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the shorthand:

```bash
fastapi dev app/main.py
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Interactive Docs

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Authentication Endpoints

#### Register User
```bash
POST /register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

#### Login
```bash
POST /token
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword
```

Returns:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

#### Get Current User
```bash
GET /me
Authorization: Bearer <access_token>
```

### File Upload Endpoints

#### Upload File (Temporary Storage)
```bash
POST /files
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <binary>
```

Returns:
```json
{
  "id": "abc123",
  "url": "/files/abc123",
  "expires_in_seconds": 900
}
```

**Note**: Files expire after 15 minutes and are automatically cleaned up.

#### Get File
```bash
GET /files/{file_id}
```

### Generation Endpoints

All generation endpoints require authentication via `Authorization: Bearer <token>` header.

#### 1. Mock Create (Device/Billboard Mockups)

Generate mockups with optional animation.

```bash
POST /api/mock_create
Content-Type: application/json
Authorization: Bearer <token>

{
  "prompt": "Modern billboard on city street at golden hour with fish-themed poster design",
  "images": ["/files/abc123"],
  "aspect_ratio": "16:9",
}
```

**Response**:
```json
{
  "status": "completed",
  "assets": [
    {
      "kind": "image",
      "url": "https://cdn.higgsfield.ai/...",
      "meta": {"type": "image"}
    },
    {
      "kind": "video",
      "url": "https://cdn.higgsfield.ai/...",
      "meta": {"type": "video", "dur": 8}
    }
  ],
  "job_set_id": "uuid",
  "provider": "higgsfield"
}
```

**Use Cases**:
- Device mockups (laptop, mobile, tablet)
- Billboard/poster placements
- UX design showcases

#### 2. Stock Image Generation

Generate brand-safe stock images.

```bash
POST /api/stock_image
Content-Type: application/json
Authorization: Bearer <token>

{
  "prompt": "Professional workspace with natural lighting",
  "aspect_ratio": "16:9",
  "images": []
}
```

**Response**:
```json
{
  "status": "completed",
  "assets": [
    {
      "kind": "image",
      "url": "https://cdn.higgsfield.ai/..."
    }
  ],
  "job_set_id": "uuid"
}
```

#### 3. Stock Video Generation

Generate videos from text or images.

```bash
POST /api/stock_video
Content-Type: application/json
Authorization: Bearer <token>

{
  "prompt": "Subtle parallax pan over modern cityscape",
  "images": ["/files/xyz789"],  // Optional: if provided, uses Image-to-Video
  "aspect_ratio": "16:9",
}
```

**Response**:
```json
{
  "status": "completed",
  "assets": [
    {
      "kind": "video",
      "url": "https://cdn.higgsfield.ai/...",
      "meta": {
        "type": "video",
        "dur": 8,
        "aspect": "16:9"
      }
    }
  ]
}
```

## 🏗️ Architecture

### Request Flow

```
Frontend/Figma Plugin
    ↓
1. Upload images → POST /files → Get temporary URLs
    ↓
2. Submit generation request → POST /api/mock_create (or stock_image/stock_video)
    ↓
Backend
    ↓
3. Forward to Higgsfield API (Nano Banana / Veo 3 / Kling)
    ↓
4. Poll for completion
    ↓
5. Return normalized response
    ↓
Frontend (receives result URLs)
```

### Key Design Choices

1. **No Permanent Storage**: Files stored in-memory with 15min TTL
2. **Stateless**: Only user auth stored in SQLite
3. **Direct Pass-through**: Minimal transformation, fast response
4. **Normalized Response**: Same format for images and videos

### Technology Stack

- **FastAPI**: Modern async web framework
- **SQLAlchemy**: ORM for user management
- **SQLite**: Lightweight database (users only)
- **httpx**: Async HTTP client for Higgsfield API
- **Pydantic**: Data validation
- **JWT**: Token-based authentication

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./app.db` |
| `SECRET_KEY` | JWT secret key | `jwt-key` (change in prod!) |
| `TOKEN_EXPIRE_MINUTES` | JWT token expiry | `30` |
| `HIGGSFIELD_API_KEY` | Higgsfield API key | *required* |
| `HIGGSFIELD_API_SECRET` | Higgsfield API secret | *required* |
| `HIGGSFIELD_BASE_URL` | Higgsfield API endpoint | `https://platform.higgsfield.ai/v1` |
| `MAX_UPLOAD_SIZE` | Max file size in bytes | `10485760` (10MB) |

## 🐳 Docker Deployment

### Using Docker Compose

```bash
docker-compose up --build
```

The service will be available at `http://localhost:8000`

### Manual Docker Build

```bash
docker build -t hacknu-back .
docker run -p 8000:8000 \
  -e HIGGSFIELD_API_KEY=your-key \
  -e HIGGSFIELD_API_SECRET=your-secret \
  hacknu-back
```

## 🧪 Testing

### Quick Health Check

```bash
curl http://localhost:8000/
```

### Register and Test Generation

```bash
# 1. Register
TOKEN=$(curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' \
  | jq -r '.access_token')

# 2. Upload image (optional)
curl -X POST http://localhost:8000/files \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@design.png"

# 3. Generate mockup
curl -X POST http://localhost:8000/api/mock_create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Modern laptop on desk with plant",
    "aspect_ratio": "16:9"
  }'
```

## 📁 Project Structure

```
hacknu-back/
├── app/
│   ├── api/
│   │   ├── __init__.py          # Router aggregation
│   │   ├── user.py              # Auth endpoints
│   │   ├── files.py             # File upload/serve
│   │   └── generate.py          # AI generation endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── higgsfield.py        # Higgsfield API client
│   ├── config.py                # Settings management
│   ├── database.py              # DB setup
│   ├── models.py                # SQLAlchemy models
│   ├── schemas.py               # Pydantic schemas
│   ├── auth.py                  # JWT auth logic
│   ├── utils.py                 # Utilities
│   └── main.py                  # FastAPI app
├── .env.example                 # Environment template
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker image
├── docker-compose.yml           # Docker compose config
└── README.md                    # This file
```

## 🚨 Error Handling

The API returns standard HTTP error codes:

- `400`: Bad request (invalid input)
- `401`: Unauthorized (missing/invalid token)
- `404`: Not found
- `410`: Gone (expired file)
- `500`: Internal server error
- `502`: Higgsfield API error
- `504`: Generation timeout

Example error response:
```json
{
  "detail": "Higgsfield API error: Rate limit exceeded"
}
```

## 🔒 Security Notes

### For Development
- Default `SECRET_KEY` is insecure - change it!
- CORS is set to `*` (all origins) - restrict in production
- SQLite with `check_same_thread=False` is for dev only

### For Production
1. Use a strong random `SECRET_KEY`
2. Configure specific CORS origins
3. Use PostgreSQL or MySQL instead of SQLite
4. Enable HTTPS
5. Add rate limiting
6. Implement proper logging and monitoring
7. Use Redis for file storage instead of in-memory

## 📝 License

[Your License Here]

## 👥 Team

HackNU Dropouts

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

Made with ❤️ for HackNU 2025