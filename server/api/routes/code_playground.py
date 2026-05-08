"""
Code Playground API Routes

Provides endpoints for the interactive code editor feature:
- Template listing
- Template execution
- Demo dataset access
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
import time
from collections import defaultdict

# Import datavint library functions
import datavint as vint

logger = logging.getLogger(__name__)

router = APIRouter()


# Simple in-memory rate limiter
class RateLimiter:
    """
    Simple in-memory rate limiter.

    Tracks requests per IP address with a sliding window.
    """
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()

        # Clean old requests outside the window
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < self.window_seconds
        ]

        # Check if under limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return False

        # Record this request
        self.requests[client_ip].append(now)
        return True

    def get_retry_after(self, client_ip: str) -> int:
        """Get seconds until rate limit resets."""
        if not self.requests[client_ip]:
            return 0

        oldest_request = min(self.requests[client_ip])
        return int(self.window_seconds - (time.time() - oldest_request)) + 1


# Initialize rate limiter: 10 requests per minute per IP
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


# Request/Response models
class ExecuteTemplateRequest(BaseModel):
    template_id: str


class ExecuteTemplateResponse(BaseModel):
    success: bool
    output: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class Template(BaseModel):
    id: str
    name: str
    description: str
    code: str
    dataset: str


class TemplateListResponse(BaseModel):
    templates: list[Template]


# Template registry
TEMPLATES = {
    'titanic': {
        'name': 'Titanic Dataset Profiling',
        'description': 'Analyze Kaggle Titanic dataset for data quality issues including missing values, duplicates, and class imbalance',
        'code': '''import datavint as vint

# Load Titanic dataset from demo data
df = vint.load_demo_dataset('titanic')

# Run comprehensive data quality checks
stats, issues = vint.profile(df)

# Display interactive results
print(f"Dataset shape: {df.shape}")
print(f"Found {len(issues)} data quality issues")

# Return results for visualization
stats, issues''',
        'dataset': 'titanic'
    }
}


@router.get("/api/code/templates", response_model=TemplateListResponse)
async def list_templates():
    """
    List all available code templates.

    Returns a list of pre-defined code templates that users can execute
    in the Code Playground.

    Returns:
        TemplateListResponse: List of available templates with metadata
    """
    templates = []
    for template_id, template_data in TEMPLATES.items():
        templates.append(Template(
            id=template_id,
            name=template_data['name'],
            description=template_data['description'],
            code=template_data['code'],
            dataset=template_data['dataset']
        ))

    return TemplateListResponse(templates=templates)


@router.post("/api/code/execute-template", response_model=ExecuteTemplateResponse)
async def execute_template(request: ExecuteTemplateRequest, http_request: Request):
    """
    Execute a pre-defined code template.

    This endpoint runs a hardcoded template (no arbitrary code execution)
    and returns the profiling results for visualization.

    Rate limit: 10 requests per minute per IP

    Args:
        request: ExecuteTemplateRequest with template_id
        http_request: FastAPI Request for client IP

    Returns:
        ExecuteTemplateResponse with execution results

    Raises:
        HTTPException 404: Template not found
        HTTPException 429: Rate limit exceeded
        HTTPException 500: Execution error
    """
    # Get client IP for rate limiting
    client_ip = http_request.client.host if http_request.client else "unknown"

    # Check rate limit
    if not rate_limiter.is_allowed(client_ip):
        retry_after = rate_limiter.get_retry_after(client_ip)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

    template_id = request.template_id

    # Validate template exists
    if template_id not in TEMPLATES:
        available = ', '.join(TEMPLATES.keys())
        raise HTTPException(
            status_code=404,
            detail=f"Template '{template_id}' not found. Available: {available}"
        )

    template = TEMPLATES[template_id]

    try:
        # Load demo dataset
        logger.info(f"Loading demo dataset: {template['dataset']}")
        df = vint.load_demo_dataset(template['dataset'])

        # Run profiling (return dict for JSON serialization)
        logger.info(f"Running profile on {template['dataset']} dataset")
        result = vint.profile(df, return_dict=True)

        # Format success response
        return ExecuteTemplateResponse(
            success=True,
            output=f"✅ Profiling complete\n"
                   f"Dataset: {template['dataset']}\n"
                   f"Shape: {result['summary']['num_rows']} rows × {result['summary']['num_columns']} columns\n"
                   f"Issues found: {result['summary']['num_issues']}",
            data=result
        )

    except FileNotFoundError as e:
        logger.error(f"Dataset file not found: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)  # Include detailed error message from datavint
        )

    except Exception as e:
        logger.error(f"Template execution failed: {e}", exc_info=True)
        return ExecuteTemplateResponse(
            success=False,
            output="",
            error=f"Execution failed: {str(e)}"
        )


@router.get("/api/code/health")
async def code_playground_health():
    """
    Health check endpoint for code playground service.

    Returns:
        dict: Service status and available datasets
    """
    try:
        # Verify demo datasets are accessible
        datasets_status = {}
        for name in vint.DEMO_DATASETS.keys():
            try:
                df = vint.load_demo_dataset(name)
                datasets_status[name] = {
                    "status": "available",
                    "shape": list(df.shape)
                }
            except Exception as e:
                datasets_status[name] = {
                    "status": "error",
                    "error": str(e)
                }

        return {
            "service": "code-playground",
            "status": "healthy",
            "templates_count": len(TEMPLATES),
            "datasets": datasets_status
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "service": "code-playground",
            "status": "unhealthy",
            "error": str(e)
        }
