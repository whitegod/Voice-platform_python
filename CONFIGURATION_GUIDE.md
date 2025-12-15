# Voice-as-a-Service Platform - Configuration Guide

## Overview
This document describes the environment-based configuration system for the VaaS platform. All hard-coded values have been moved to environment variables for better flexibility and security.

## Setup Instructions

### 1. Create Environment File
Copy the template file to create your own environment configuration:

```bash
cp config.env.example .env
```

### 2. Update Configuration Values
Edit the `.env` file with your specific values:

```bash
# Required: Add your API keys
OPENAI_API_KEY=your_actual_openai_key
POSTGRES_PASSWORD=your_secure_password

# Optional: Customize other settings as needed
```

### 3. Load Environment Variables
The application automatically loads environment variables from `.env` file using `python-dotenv`.

## Configuration Categories

### Application Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `8000` | API server port |

### AI Core - Whisper ASR
| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_MODEL` | `base` | Whisper model size (tiny, base, small, medium, large) |
| `WHISPER_DEVICE` | `cpu` | Device for inference (cpu, cuda) |
| `WHISPER_LANGUAGE` | `en` | Default language code |

### AI Core - Text-to-Speech
| Variable | Default | Description |
|----------|---------|-------------|
| `TTS_MODEL` | `tts_models/en/ljspeech/tacotron2-DDC` | TTS model name |
| `TTS_DEVICE` | `cpu` | Device for inference (cpu, cuda) |

### AI Core - LLM
| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | LLM provider (openai, anthropic, etc.) |
| `OPENAI_MODEL` | `gpt-4-turbo-preview` | Model name |
| `OPENAI_API_KEY` | **Required** | OpenAI API key |
| `LLM_TEMPERATURE` | `0.7` | Generation temperature (0.0-1.0) |
| `LLM_MAX_TOKENS` | `2000` | Maximum tokens in response |
| `DEFAULT_SYSTEM_PROMPT` | `You are a helpful assistant.` | Default system prompt |

### AI Core - NLU (Rasa)
| Variable | Default | Description |
|----------|---------|-------------|
| `RASA_ENDPOINT` | `http://localhost:5005` | Rasa server endpoint |

### AI Core - Content Moderation
| Variable | Default | Description |
|----------|---------|-------------|
| `DETOXIFY_MODEL` | `original` | Detoxify model variant |
| `MODERATION_THRESHOLD` | `0.7` | Threshold for flagging content |

### Redis Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `localhost` | Redis server host |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_DB` | `0` | Redis database number |
| `REDIS_PASSWORD` | *(empty)* | Redis password |
| `REDIS_SESSION_TTL` | `3600` | Session TTL in seconds |
| `REDIS_NAMESPACE` | `vaas` | Key namespace prefix |

### PostgreSQL Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `localhost` | PostgreSQL server host |
| `POSTGRES_PORT` | `5432` | PostgreSQL server port |
| `POSTGRES_DB` | `vaas_platform` | Database name |
| `POSTGRES_USER` | `vaas_user` | Database user |
| `POSTGRES_PASSWORD` | **Required** | Database password |
| `POSTGRES_MIN_POOL_SIZE` | `5` | Minimum connection pool size |
| `POSTGRES_MAX_POOL_SIZE` | `20` | Maximum connection pool size |

### Qdrant Vector Database
| Variable | Default | Description |
|----------|---------|-------------|
| `QDRANT_HOST` | `localhost` | Qdrant server host |
| `QDRANT_PORT` | `6333` | Qdrant server port |
| `QDRANT_API_KEY` | *(empty)* | Qdrant API key |
| `QDRANT_COLLECTION_NAME` | `vaas_embeddings` | Default collection name |
| `QDRANT_VECTOR_SIZE` | `384` | Vector dimension size |
| `QDRANT_EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `QDRANT_DISTANCE_METRIC` | `cosine` | Distance metric (cosine, dot, euclid) |

### Domain Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `DOMAIN_CONFIG_PATH` | `config/domains` | Path to domain configuration files |

### API Rate Limiting
| Variable | Default | Description |
|----------|---------|-------------|
| `API_RATE_LIMIT_PER_MINUTE` | `60` | Max requests per minute per tenant |
| `API_RATE_LIMIT_PER_HOUR` | `1000` | Max requests per hour per tenant |

### Data Adapter (External APIs)
| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_ADAPTER_TIMEOUT` | `30` | HTTP request timeout in seconds |
| `DATA_ADAPTER_MAX_RETRIES` | `3` | Maximum retry attempts |
| `DATA_ADAPTER_USER_AGENT` | `VaaS-Platform/1.0` | User-Agent header |

### Policy and Compliance
| Variable | Default | Description |
|----------|---------|-------------|
| `REQUIRE_MODERATION` | `true` | Require content moderation |

### Analytics
| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_ANALYTICS` | `true` | Enable analytics tracking |

### CORS Configuration
| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ALLOW_ORIGINS` | `*` | Allowed origins (use comma-separated for multiple, e.g., `https://example.com,https://example2.com`) |
| `CORS_ALLOW_CREDENTIALS` | `true` | Allow credentials |
| `CORS_ALLOW_METHODS` | `*` | Allowed HTTP methods (use comma-separated for multiple, e.g., `GET,POST,PUT`) |
| `CORS_ALLOW_HEADERS` | `*` | Allowed headers (use comma-separated for multiple, e.g., `Content-Type,Authorization`) |

### File Paths
| Variable | Default | Description |
|----------|---------|-------------|
| `LOGS_DIR` | `logs` | Directory for log files |
| `TMP_DIR` | `tmp` | Directory for temporary files |
| `MODELS_DIR` | `models` | Directory for model cache |

## Environment-Specific Configuration

### Development
```bash
LOG_LEVEL=DEBUG
API_HOST=localhost
API_PORT=8000
WHISPER_DEVICE=cpu
TTS_DEVICE=cpu
```

### Production
```bash
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=80
WHISPER_DEVICE=cuda
TTS_DEVICE=cuda
POSTGRES_MIN_POOL_SIZE=10
POSTGRES_MAX_POOL_SIZE=50
REDIS_SESSION_TTL=7200
```

### Docker Deployment
When using Docker, set environment variables in `docker-compose.yml`:

```yaml
services:
  vaas-api:
    environment:
      - POSTGRES_HOST=postgres
      - REDIS_HOST=redis
      - QDRANT_HOST=qdrant
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

## Security Best Practices

1. **Never commit `.env` files** - Add `.env` to `.gitignore`
2. **Use strong passwords** - Generate secure random passwords for database access
3. **Rotate API keys** - Regularly update API keys and secrets
4. **Restrict CORS origins** - In production, specify exact allowed origins instead of `*`
5. **Use environment variables** - For sensitive data in CI/CD pipelines
6. **Enable TLS/SSL** - Use HTTPS in production environments

## Validation

Test your configuration:

```python
from dotenv import load_dotenv
import os

load_dotenv()

# Verify required variables
required_vars = ['OPENAI_API_KEY', 'POSTGRES_PASSWORD']
for var in required_vars:
    if not os.getenv(var):
        print(f"⚠️  Missing required variable: {var}")
    else:
        print(f"✓ {var} is set")
```

## Troubleshooting

### Issue: Environment variables not loading
**Solution:** Ensure `.env` file is in the project root directory and `python-dotenv` is installed.

### Issue: Default values being used
**Solution:** Check `.env` file syntax - ensure no spaces around `=` sign.

### Issue: Database connection fails
**Solution:** Verify database credentials and ensure the database server is accessible.

### Issue: API key errors
**Solution:** Confirm API keys are valid and have not expired.

## Migration from Hard-coded Values

All previously hard-coded values have been moved to environment variables:

- ✅ Database connection pool sizes
- ✅ Redis namespace
- ✅ LLM temperature
- ✅ Data adapter timeouts and retries
- ✅ Default system prompts
- ✅ CORS configuration
- ✅ File paths
- ✅ User-Agent strings
- ✅ Embedding models and vector dimensions

## Additional Resources

- [Python-dotenv Documentation](https://github.com/theskumar/python-dotenv)
- [12-Factor App Config](https://12factor.net/config)
- [Environment Variable Best Practices](https://docs.docker.com/compose/environment-variables/)

---

**Note:** This configuration system provides flexibility while maintaining security. Always follow security best practices when managing environment variables in production systems.

