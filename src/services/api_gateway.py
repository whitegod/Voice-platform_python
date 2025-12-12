"""
API Gateway
FastAPI-based REST API gateway for VaaS platform
"""

import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Header, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
from pathlib import Path
import uuid

from .tenant_manager import TenantManager
from .orchestrator import PipelineOrchestrator

logger = logging.getLogger(__name__)


# Request/Response Models
class TextRequest(BaseModel):
    """Text processing request"""
    text: str = Field(..., description="Input text to process")
    user_id: str = Field(..., description="User identifier")
    domain: str = Field(..., description="Domain name (e.g., real_estate, food_delivery)")
    session_id: Optional[str] = Field(None, description="Existing session ID")
    return_audio: bool = Field(False, description="Whether to return audio response")


class VoiceRequest(BaseModel):
    """Voice processing request metadata"""
    user_id: str
    domain: str
    session_id: Optional[str] = None
    return_audio: bool = True


class ProcessResponse(BaseModel):
    """Processing response"""
    success: bool
    text_response: str
    audio_url: Optional[str] = None
    intent: Optional[str] = None
    entities: Optional[dict] = None
    session_id: Optional[str] = None
    metadata: Optional[dict] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    services: dict


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None


# API Gateway Application
class APIGateway:
    """
    FastAPI-based API Gateway.
    Handles authentication, routing, and request processing.
    """

    def __init__(
        self,
        orchestrator: PipelineOrchestrator,
        tenant_manager: TenantManager,
        host: str = "0.0.0.0",
        port: int = 8000
    ):
        """
        Initialize API Gateway.

        Args:
            orchestrator: Pipeline orchestrator instance
            tenant_manager: Tenant manager instance
            host: Server host
            port: Server port
        """
        self.orchestrator = orchestrator
        self.tenant_manager = tenant_manager
        self.host = host
        self.port = port
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Voice-as-a-Service API",
            description="Multi-domain conversational AI platform",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self._register_routes()
        
        logger.info(f"APIGateway initialized on {host}:{port}")

    async def verify_api_key(
        self,
        authorization: Optional[str] = Header(None)
    ) -> str:
        """
        Dependency to verify API key and extract tenant ID.

        Args:
            authorization: Authorization header

        Returns:
            Tenant ID

        Raises:
            HTTPException: If authentication fails
        """
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header"
            )

        # Extract API key from "Bearer <api_key>"
        try:
            scheme, api_key = authorization.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid scheme")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization format. Use: Bearer <api_key>"
            )

        # Verify API key
        tenant_id = await self.tenant_manager.verify_api_key(api_key)
        
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )

        return tenant_id

    def _register_routes(self):
        """Register all API routes"""

        @self.app.get("/", tags=["Root"])
        async def root():
            """Root endpoint"""
            return {
                "service": "Voice-as-a-Service Platform",
                "version": "1.0.0",
                "status": "running"
            }

        @self.app.get("/health", response_model=HealthResponse, tags=["Health"])
        async def health_check():
            """Health check endpoint"""
            try:
                health = await self.orchestrator.health_check()
                
                status_str = "healthy" if health["overall"] else "degraded"
                
                return HealthResponse(
                    status=status_str,
                    services=health
                )
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return HealthResponse(
                    status="unhealthy",
                    services={"error": str(e)}
                )

        @self.app.post(
            "/api/v1/process/text",
            response_model=ProcessResponse,
            tags=["Processing"]
        )
        async def process_text(
            request: TextRequest,
            tenant_id: str = Depends(self.verify_api_key)
        ):
            """
            Process text input.

            Args:
                request: Text processing request
                tenant_id: Verified tenant ID from API key

            Returns:
                Processing result
            """
            try:
                logger.info(f"Processing text request for tenant {tenant_id}")

                # Process through orchestrator
                result = await self.orchestrator.process_text(
                    text=request.text,
                    user_id=request.user_id,
                    tenant_id=tenant_id,
                    domain=request.domain,
                    session_id=request.session_id
                )

                # Generate audio if requested
                audio_url = None
                if request.return_audio:
                    audio_path = Path(f"tmp/audio_{uuid.uuid4()}.wav")
                    audio_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    self.orchestrator.tts.synthesize(
                        result.text_response,
                        output_path=audio_path
                    )
                    
                    audio_url = f"/api/v1/audio/{audio_path.name}"

                return ProcessResponse(
                    success=True,
                    text_response=result.text_response,
                    audio_url=audio_url,
                    intent=result.intent,
                    entities=result.entities,
                    session_id=result.metadata.get("session_id"),
                    metadata=result.metadata
                )

            except Exception as e:
                logger.error(f"Text processing failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.app.post(
            "/api/v1/process/voice",
            response_model=ProcessResponse,
            tags=["Processing"]
        )
        async def process_voice(
            audio_file: UploadFile = File(...),
            user_id: str = Header(...),
            domain: str = Header(...),
            session_id: Optional[str] = Header(None),
            return_audio: bool = Header(True),
            tenant_id: str = Depends(self.verify_api_key)
        ):
            """
            Process voice input.

            Args:
                audio_file: Audio file upload
                user_id: User identifier (header)
                domain: Domain name (header)
                session_id: Session ID (header)
                return_audio: Return audio response (header)
                tenant_id: Verified tenant ID

            Returns:
                Processing result
            """
            try:
                logger.info(f"Processing voice request for tenant {tenant_id}")

                # Save uploaded file
                audio_path = Path(f"tmp/upload_{uuid.uuid4()}.wav")
                audio_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(audio_path, "wb") as f:
                    content = await audio_file.read()
                    f.write(content)

                # Process through orchestrator
                result = await self.orchestrator.process_voice(
                    audio_path=audio_path,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    domain=domain,
                    session_id=session_id,
                    return_audio=return_audio
                )

                # Clean up uploaded file
                audio_path.unlink()

                # Prepare response
                audio_url = None
                if result.audio_response:
                    audio_url = f"/api/v1/audio/{result.audio_response.name}"

                return ProcessResponse(
                    success=True,
                    text_response=result.text_response,
                    audio_url=audio_url,
                    intent=result.intent,
                    entities=result.entities,
                    session_id=result.metadata.get("session_id"),
                    metadata=result.metadata
                )

            except Exception as e:
                logger.error(f"Voice processing failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.app.get("/api/v1/audio/{filename}", tags=["Audio"])
        async def get_audio(filename: str):
            """
            Download audio file.

            Args:
                filename: Audio filename

            Returns:
                Audio file
            """
            try:
                audio_path = Path(f"tmp/{filename}")
                
                if not audio_path.exists():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Audio file not found"
                    )

                return FileResponse(
                    path=audio_path,
                    media_type="audio/wav",
                    filename=filename
                )

            except Exception as e:
                logger.error(f"Audio retrieval failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.app.get("/api/v1/domains", tags=["Configuration"])
        async def list_domains(tenant_id: str = Depends(self.verify_api_key)):
            """
            List available domains.

            Args:
                tenant_id: Verified tenant ID

            Returns:
                List of domain names
            """
            try:
                domains = self.orchestrator.config_manager.list_domains()
                return {"domains": domains}

            except Exception as e:
                logger.error(f"Failed to list domains: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )

        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc):
            """Custom HTTP exception handler"""
            return JSONResponse(
                status_code=exc.status_code,
                content=ErrorResponse(
                    error=exc.detail,
                    detail=str(exc)
                ).dict()
            )

        @self.app.exception_handler(Exception)
        async def general_exception_handler(request, exc):
            """General exception handler"""
            logger.error(f"Unhandled exception: {exc}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse(
                    error="Internal server error",
                    detail=str(exc)
                ).dict()
            )

    def run(self):
        """Run the API server"""
        import uvicorn
        
        logger.info(f"Starting API Gateway on {self.host}:{self.port}")
        
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )

