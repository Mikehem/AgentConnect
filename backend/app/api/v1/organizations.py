"""Organization API endpoints."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.user import User
from app.models.organization import Organization
from app.schemas.organization import (
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    OrganizationListResponse, OrganizationQuotas, OrganizationSettings
)

logger = get_logger(__name__)
router = APIRouter()


# Temporary mock for authentication - replace with proper auth
def get_current_user() -> User:
    """Temporary mock for current user."""
    from app.models.user import User
    
    # Create mock user for testing
    user = User(
        id=uuid.uuid4(),
        org_id=uuid.uuid4(),
        email="test@example.com",
        name="Test User",
        roles=["admin"],
        status="active"
    )
    
    return user


@router.post(
    "/",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Organization",
    description="Create a new organization."
)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> OrganizationResponse:
    """Create a new organization."""
    # Check for duplicate slug
    existing_org = db.query(Organization).filter(
        Organization.slug == org_data.slug
    ).first()
    
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization with this slug already exists"
        )
    
    # Create organization
    org = Organization(
        id=uuid.uuid4(),
        name=org_data.name,
        slug=org_data.slug,
        subscription_tier=org_data.subscription_tier,
        settings=org_data.settings or {}
    )
    
    db.add(org)
    db.commit()
    db.refresh(org)
    
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        subscription_tier=org.subscription_tier,
        status=org.status,
        created_at=org.created_at,
        updated_at=org.updated_at
    )


@router.get(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Get Organization",
    description="Get organization details by ID."
)
async def get_organization(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> OrganizationResponse:
    """Get organization by ID."""
    try:
        org_uuid = uuid.UUID(org_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format"
        )
    
    org = db.query(Organization).filter(Organization.id == org_uuid).first()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        subscription_tier=org.subscription_tier,
        status=org.status,
        settings=org.settings or {},
        created_at=org.created_at,
        updated_at=org.updated_at
    )


@router.patch(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Update Organization",
    description="Update organization details."
)
async def update_organization(
    org_id: str,
    org_data: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> OrganizationResponse:
    """Update organization."""
    try:
        org_uuid = uuid.UUID(org_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format"
        )
    
    org = db.query(Organization).filter(Organization.id == org_uuid).first()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Update fields
    if org_data.name is not None:
        org.name = org_data.name
    if org_data.slug is not None:
        # Check for duplicate slug
        existing_org = db.query(Organization).filter(
            Organization.slug == org_data.slug,
            Organization.id != org_id
        ).first()
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization with this slug already exists"
            )
        org.slug = org_data.slug
    if org_data.subscription_tier is not None:
        org.subscription_tier = org_data.subscription_tier
    if org_data.settings is not None:
        org.settings = org_data.settings
    
    db.commit()
    db.refresh(org)
    
    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        subscription_tier=org.subscription_tier,
        status=org.status,
        settings=org.settings or {},
        created_at=org.created_at,
        updated_at=org.updated_at
    )


@router.delete(
    "/{org_id}",
    response_model=dict,
    summary="Delete Organization",
    description="Delete an organization."
)
async def delete_organization(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Delete organization."""
    try:
        org_uuid = uuid.UUID(org_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format"
        )
    
    org = db.query(Organization).filter(Organization.id == org_uuid).first()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    db.delete(org)
    db.commit()
    
    return {"message": "Organization deleted successfully"}


@router.get(
    "/",
    response_model=OrganizationListResponse,
    summary="List Organizations",
    description="List organizations with filtering and pagination."
)
async def list_organizations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    subscription_tier: Optional[str] = Query(None, description="Filter by subscription tier"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> OrganizationListResponse:
    """List organizations with optional filtering."""
    query = db.query(Organization)
    
    if status:
        query = query.filter(Organization.status == status)
    if subscription_tier:
        query = query.filter(Organization.subscription_tier == subscription_tier)
    
    total = query.count()
    orgs = query.offset(skip).limit(limit).all()
    
    return OrganizationListResponse(
        organizations=[
            OrganizationResponse(
                id=org.id,
                name=org.name,
                slug=org.slug,
                subscription_tier=org.subscription_tier,
                status=org.status,
                created_at=org.created_at,
                updated_at=org.updated_at
            ) for org in orgs
        ],
        total=total,
        limit=limit,
        offset=skip,
        has_more=skip + limit < total
    )


@router.get(
    "/{org_id}/quotas",
    response_model=OrganizationQuotas,
    summary="Get Organization Quotas",
    description="Get organization quotas and limits."
)
async def get_organization_quotas(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> OrganizationQuotas:
    """Get organization quotas."""
    try:
        org_uuid = uuid.UUID(org_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format"
        )
    
    org = db.query(Organization).filter(Organization.id == org_uuid).first()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Return default quotas for now
    return OrganizationQuotas(
        server_limit=100,
        user_limit=50,
        storage_limit_gb=100,
        api_rate_limit=1000,
        current_servers=0,  # TODO: Calculate actual count
        current_users=0     # TODO: Calculate actual count
    )


@router.patch(
    "/{org_id}/quotas",
    response_model=OrganizationQuotas,
    summary="Update Organization Quotas",
    description="Update organization quotas and limits."
)
async def update_organization_quotas(
    org_id: str,
    quotas: OrganizationQuotas,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> OrganizationQuotas:
    """Update organization quotas."""
    try:
        org_uuid = uuid.UUID(org_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format"
        )
    
    org = db.query(Organization).filter(Organization.id == org_uuid).first()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Update quotas in settings
    if not org.settings:
        org.settings = {}
    
    org.settings["quotas"] = quotas.model_dump()
    db.commit()
    
    return quotas


@router.get(
    "/{org_id}/settings",
    response_model=OrganizationSettings,
    summary="Get Organization Settings",
    description="Get organization settings and configuration."
)
async def get_organization_settings(
    org_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> OrganizationSettings:
    """Get organization settings."""
    try:
        org_uuid = uuid.UUID(org_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format"
        )
    
    org = db.query(Organization).filter(Organization.id == org_uuid).first()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return OrganizationSettings(
        settings=org.settings or {}
    )


@router.patch(
    "/{org_id}/settings",
    response_model=OrganizationSettings,
    summary="Update Organization Settings",
    description="Update organization settings and configuration."
)
async def update_organization_settings(
    org_id: str,
    settings_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> OrganizationSettings:
    """Update organization settings."""
    try:
        org_uuid = uuid.UUID(org_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID format"
        )
    
    org = db.query(Organization).filter(Organization.id == org_uuid).first()
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Update settings
    org.settings = settings_data
    db.commit()
    
    return OrganizationSettings(settings=settings_data)
