# AgenticAI Deployment Guide

This guide provides comprehensive instructions for deploying the AgenticAI application in various environments.

## 🚀 Local Development Deployment

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd AgenticAI
   ```

2. **Set up Python environment**:
   ```bash
   # Using pipenv (recommended)
   pipenv install --dev
   pipenv shell
   
   # Or using pip with virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up frontend dependencies**:
   ```bash
   cd ui
   npm install
   cd ..
   ```

4. **Configure environment variables**:
   Copy `.env.example` to `.env` and configure your settings:
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

5. **Run the application**:
   ```bash
   # Terminal 1: Start the backend
   python -m app.main
   
   # Terminal 2: Start the frontend development server
   cd ui
   npm run dev
   ```

## ☁️ Cloud Deployment Options

### AWS Deployment

#### Option 1: AWS Elastic Beanstalk
1. Prepare application bundle:
   ```bash
   # Create a zip file with your application code
   zip -r agenticai.zip . -x "*.git*" "*__pycache__*" "*venv*" "*node_modules*"
   ```

2. Deploy using Elastic Beanstalk CLI:
   ```bash
   eb init
   eb create agenticai-env
   eb deploy
   ```

#### Option 2: AWS ECS with Fargate
1. Build and push Docker images to ECR (if you choose to use Docker):
   ```bash
   # Build the images
   docker build -t agenticai-backend -f Dockerfile.backend .
   docker build -t agenticai-frontend -f ui/Dockerfile .
   
   # Tag and push to ECR
   aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.<region>.amazonaws.com
   docker tag agenticai-backend:latest <aws_account_id>.dkr.ecr.<region>.amazonaws.com/agenticai-backend:latest
   docker tag agenticai-frontend:latest <aws_account_id>.dkr.ecr.<region>.amazonaws.com/agenticai-frontend:latest
   docker push <aws_account_id>.dkr.ecr.<region>.amazonaws.com/agenticai-backend:latest
   docker push <aws_account_id>.dkr.ecr.<region>.amazonaws.com/agenticai-frontend:latest
   ```

2. Create ECS task definitions and services using the pushed images.

### Google Cloud Platform Deployment

#### Option 1: Google Cloud Run
1. Build and push container images:
   ```bash
   # Build the images
   gcloud builds submit --tag gcr.io/<project-id>/agenticai-backend
   gcloud builds submit --tag gcr.io/<project-id>/agenticai-frontend
   ```

2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy agenticai-backend --image gcr.io/<project-id>/agenticai-backend --platform managed
   gcloud run deploy agenticai-frontend --image gcr.io/<project-id>/agenticai-frontend --platform managed
   ```

#### Option 2: Google Kubernetes Engine (GKE)
1. Create a GKE cluster:
   ```bash
   gcloud container clusters create agenticai-cluster --num-nodes=3
   ```

2. Deploy using Kubernetes manifests (you would need to create these):
   ```bash
   kubectl apply -f k8s/
   ```

### Azure Deployment

#### Option 1: Azure App Service
1. Create App Service instances for both backend and frontend:
   ```bash
   az webapp create --resource-group <resource-group> --plan <app-service-plan> --name agenticai-backend
   az webapp create --resource-group <resource-group> --plan <app-service-plan> --name agenticai-frontend
   ```

2. Deploy the code:
   ```bash
   az webapp deployment source config-zip --resource-group <resource-group> --name agenticai-backend --src agenticai-backend.zip
   az webapp deployment source config-zip --resource-group <resource-group> --name agenticai-frontend --src agenticai-frontend.zip
   ```

#### Option 2: Azure Container Instances
1. Deploy container images:
   ```bash
   az container create --resource-group <resource-group> --name agenticai-backend --image <container-registry>/agenticai-backend --dns-name-label agenticai-backend --ports 8000
   az container create --resource-group <resource-group> --name agenticai-frontend --image <container-registry>/agenticai-frontend --dns-name-label agenticai-frontend --ports 5173
   ```

## 🛠️ Environment Configuration

### Backend Configuration
The backend reads configuration from environment variables. Key variables include:

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `CORS_ORIGINS`: Comma-separated list of allowed CORS origins
- LLM provider API keys (GOOGLE_API_KEY, OPENAI_API_KEY, etc.)
- Database configuration

### Frontend Configuration
The frontend uses Vite environment variables with the `VITE_` prefix:

- `VITE_API_BASE_URL`: Backend API base URL
- `VITE_API_PATH`: API path prefix
- `VITE_REQUEST_TIMEOUT_MS`: Request timeout in milliseconds

## 🔄 CI/CD Pipeline

### GitHub Actions Example
```yaml
name: Deploy AgenticAI

on:
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy to cloud platform
      run: |
        # Add your deployment commands here
```

## 📊 Monitoring and Logging

### Application Monitoring
- Implement application performance monitoring (APM) with tools like New Relic or Datadog
- Set up health check endpoints
- Monitor API response times and error rates

### Log Management
- Configure structured logging
- Set up log aggregation with tools like ELK stack or cloud provider logging services
- Implement log retention policies

## 🔒 Security Considerations

### API Security
- Use HTTPS in production
- Implement proper authentication and authorization
- Validate and sanitize all input data
- Set appropriate CORS policies

### Secrets Management
- Never commit secrets to version control
- Use secret management services (AWS Secrets Manager, Azure Key Vault, etc.)
- Rotate API keys regularly

### Container Security (if using Docker)
- Use minimal base images
- Run containers as non-root users
- Scan images for vulnerabilities
- Keep base images updated

## 🆘 Troubleshooting

### Common Issues

#### Python Dependencies
**Issue**: `ModuleNotFoundError` when running the application
**Solution**: Ensure all dependencies are installed and you're in the correct virtual environment.

#### Frontend Development Server
**Issue**: Frontend fails to connect to backend
**Solution**: Check that the backend is running and CORS settings are correct.

#### LLM Provider Configuration
**Issue**: `RuntimeError: LLM_PROVIDER is not set`
**Solution**: Set the appropriate environment variables for your chosen LLM provider.

#### Database Connection
**Issue**: `sqlite3.OperationalError: unable to open database file`
**Solution**: Ensure the database directory exists and has proper permissions.

### Performance Optimization

#### Backend Optimization
- Enable database connection pooling
- Implement caching strategies for frequently accessed data
- Use asynchronous processing for long-running operations

#### Frontend Optimization
- Enable code splitting
- Optimize asset loading
- Implement efficient state management

## 📈 Scaling Considerations

### Horizontal Scaling
- Use load balancers to distribute traffic
- Implement session management for stateless scaling
- Use external databases instead of SQLite for production

### Vertical Scaling
- Monitor resource usage
- Upgrade instance sizes as needed
- Optimize database queries

## 📞 Support

For deployment issues, please check:
1. Environment variable configuration
2. Network and firewall settings
3. Resource limits (memory, CPU)
4. Dependency versions compatibility

If you continue to experience issues, please open a GitHub issue with:
- Error messages
- Environment details
- Steps to reproduce