from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user, require_admin
from app.models import User, PromptVersion
from app.schemas.prompts import (
    PromptVersionCreate, PromptVersionUpdate, PromptVersionResponse,
    SetActivePromptRequest, DuplicatePromptRequest
)
from app.services.prompts import (
    get_prompt_versions, get_active_prompt, set_active_prompt,
    create_prompt_version, duplicate_prompt
)

router = APIRouter(prefix="/prompts", tags=["Prompt Versions"])


@router.get("/", response_model=List[PromptVersionResponse])
def list_prompts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all available prompt versions (global + tenant-specific)."""
    return get_prompt_versions(db, current_user.tenant_id)


@router.get("/active", response_model=PromptVersionResponse)
def get_active(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get currently active prompt for tenant."""
    prompt = get_active_prompt(db, current_user.tenant_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="No active prompt found")
    return prompt


@router.post("/active", response_model=PromptVersionResponse)
def set_active(
    request: SetActivePromptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Set active prompt for tenant (Admin only)."""
    prompt = set_active_prompt(db, current_user.tenant_id, request.prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.post("/", response_model=PromptVersionResponse, status_code=status.HTTP_201_CREATED)
def create_prompt(
    data: PromptVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a custom prompt version (Admin only)."""
    return create_prompt_version(
        db=db,
        tenant_id=current_user.tenant_id,
        name=data.name,
        system_prompt=data.system_prompt,
        context_template=data.context_template,
        task_template=data.task_template,
        version=data.version,
        description=data.description,
        model=data.model,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
    )


@router.get("/{prompt_id}", response_model=PromptVersionResponse)
def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific prompt version."""
    prompt = db.query(PromptVersion).filter(
        PromptVersion.id == prompt_id,
        (PromptVersion.tenant_id == current_user.tenant_id) | (PromptVersion.tenant_id == None)
    ).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt


@router.put("/{prompt_id}", response_model=PromptVersionResponse)
def update_prompt(
    prompt_id: int,
    data: PromptVersionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update a tenant-specific prompt (Admin only). Cannot edit global prompts."""
    prompt = db.query(PromptVersion).filter(
        PromptVersion.id == prompt_id,
        PromptVersion.tenant_id == current_user.tenant_id  # Only tenant prompts
    ).first()

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found or cannot edit global prompts")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prompt, field, value)

    db.commit()
    db.refresh(prompt)
    return prompt


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a tenant-specific prompt (Admin only)."""
    prompt = db.query(PromptVersion).filter(
        PromptVersion.id == prompt_id,
        PromptVersion.tenant_id == current_user.tenant_id
    ).first()

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found or cannot delete global prompts")

    db.delete(prompt)
    db.commit()


@router.post("/duplicate", response_model=PromptVersionResponse, status_code=status.HTTP_201_CREATED)
def duplicate_prompt_endpoint(
    request: DuplicatePromptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Duplicate a prompt for customization (Admin only)."""
    prompt = duplicate_prompt(db, request.prompt_id, current_user.tenant_id, request.new_name)
    if not prompt:
        raise HTTPException(status_code=404, detail="Source prompt not found")
    return prompt
