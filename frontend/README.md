# Oratio Frontend

Next.js frontend for the Oratio voice agent platform.

## Environment Configuration

The frontend uses environment variables to configure the backend API URL:

- **Local Development**: Defaults to `http://localhost:8000`
- **Production**: Set via `NEXT_PUBLIC_API_URL` build argument in Docker

### Local Development

For local development, the frontend automatically connects to `http://localhost:8000`:

```bash
npm install
npm run dev
```

Make sure your backend is running on `http://localhost:8000`.

### Production Build

For production builds, the API URL is baked into the Docker image at build time:

```bash
# Build with production API URL
docker build \
  --build-arg NEXT_PUBLIC_API_URL=https://your-api-domain.com \
  -f Dockerfile.prod \
  -t oratio-frontend .
```

### Testing Production Build Locally

To test the production build locally with your local backend:

```bash
# Build without API URL (defaults to localhost:8000)
docker build -f Dockerfile.prod -t oratio-frontend .

# Run the container
docker run -p 3000:3000 oratio-frontend
```

Or to test with a specific API URL:

```bash
# Build with custom API URL
docker build \
  --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 \
  -f Dockerfile.prod \
  -t oratio-frontend .

# Run the container
docker run -p 3000:3000 oratio-frontend
```

## CI/CD

The GitHub Actions workflow automatically:

1. **Builds the frontend** with the production API URL from the `FASTAPI_BACKEND` secret:
   ```yaml
   build-args: |
     NEXT_PUBLIC_API_URL=${{ secrets.FASTAPI_BACKEND }}
   ```

2. **Invalidates CloudFront cache** after frontend deployments to ensure users get the latest version immediately

## CloudFront Cache Invalidation

### Automatic (Recommended)
CloudFront cache is automatically invalidated by GitHub Actions when frontend changes are deployed. No manual action needed! ✅

### Manual (When Needed)
For manual deployments or emergency cache clearing:

```bash
# From the project root
./scripts/invalidate_cloudfront.sh
```

This script is useful for:
- Testing cache behavior
- Manual deployments outside GitHub Actions
- Emergency cache clearing

## Architecture

- **Framework**: Next.js 15 with App Router
- **Styling**: Tailwind CSS with shadcn/ui components
- **Authentication**: JWT tokens stored in localStorage
- **API Client**: Centralized client with automatic token refresh
- **Deployment**: ECS Fargate + CloudFront CDN

## Key Features

- 🔐 Secure authentication with Cognito
- 🤖 Agent creation and management
- 📚 Knowledge base integration
- 💬 Real-time chat testing
- 🎤 Voice agent testing
- 📊 API key management
- 🎨 Modern, responsive UI

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

**Note**: `NEXT_PUBLIC_*` variables are embedded into the JavaScript bundle at build time and cannot be changed at runtime.
