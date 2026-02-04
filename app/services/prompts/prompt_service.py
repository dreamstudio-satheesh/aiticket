from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from app.models import PromptVersion
from app.services.prompts.prompt_templates import PROMPT_VERSIONS


def seed_default_prompts(db: Session) -> int:
    """Seed default prompt versions (global, tenant_id=None)."""
    created = 0

    for key, config in PROMPT_VERSIONS.items():
        # Check if already exists
        existing = db.query(PromptVersion).filter(
            PromptVersion.tenant_id == None,
            PromptVersion.version == config["version"]
        ).first()

        if not existing:
            prompt = PromptVersion(
                tenant_id=None,  # Global
                version=config["version"],
                name=config["name"],
                description=config["description"],
                system_prompt=config["system_prompt"],
                context_template=config["context_template"],
                task_template=config["task_template"],
                model=config["model"],
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
                is_active=config["is_default"],
                is_default=config["is_default"],
            )
            db.add(prompt)
            created += 1

    db.commit()
    return created


def get_prompt_versions(db: Session, tenant_id: Optional[int] = None) -> List[PromptVersion]:
    """Get all prompt versions for a tenant (includes global)."""
    return db.query(PromptVersion).filter(
        (PromptVersion.tenant_id == tenant_id) | (PromptVersion.tenant_id == None)
    ).order_by(PromptVersion.version.desc()).all()


def get_active_prompt(db: Session, tenant_id: int) -> Optional[PromptVersion]:
    """Get active prompt for tenant, fallback to global default."""
    # Tenant-specific active
    prompt = db.query(PromptVersion).filter(
        PromptVersion.tenant_id == tenant_id,
        PromptVersion.is_active == True
    ).first()

    if prompt:
        return prompt

    # Global default
    return db.query(PromptVersion).filter(
        PromptVersion.tenant_id == None,
        PromptVersion.is_default == True
    ).first()


def set_active_prompt(db: Session, tenant_id: int, prompt_id: int) -> Optional[PromptVersion]:
    """Set a prompt as active for tenant (deactivates others)."""
    prompt = db.query(PromptVersion).filter(
        PromptVersion.id == prompt_id,
        (PromptVersion.tenant_id == tenant_id) | (PromptVersion.tenant_id == None)
    ).first()

    if not prompt:
        return None

    # Deactivate all tenant prompts
    db.query(PromptVersion).filter(
        PromptVersion.tenant_id == tenant_id
    ).update({"is_active": False})

    # If selecting a global prompt, create tenant copy
    if prompt.tenant_id is None:
        tenant_prompt = PromptVersion(
            tenant_id=tenant_id,
            version=prompt.version,
            name=prompt.name,
            description=prompt.description,
            system_prompt=prompt.system_prompt,
            context_template=prompt.context_template,
            task_template=prompt.task_template,
            model=prompt.model,
            temperature=prompt.temperature,
            max_tokens=prompt.max_tokens,
            is_active=True,
            is_default=False,
        )
        db.add(tenant_prompt)
        db.commit()
        db.refresh(tenant_prompt)
        return tenant_prompt

    # Activate selected prompt
    prompt.is_active = True
    db.commit()
    db.refresh(prompt)
    return prompt


def create_prompt_version(
    db: Session,
    tenant_id: int,
    name: str,
    system_prompt: str,
    context_template: str,
    task_template: str,
    version: str = "custom",
    description: str = "",
    model: str = "gpt-4o-mini",
    temperature: int = 3,
    max_tokens: int = 1000,
) -> PromptVersion:
    """Create a custom prompt version for tenant."""
    prompt = PromptVersion(
        tenant_id=tenant_id,
        version=version,
        name=name,
        description=description,
        system_prompt=system_prompt,
        context_template=context_template,
        task_template=task_template,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        is_active=False,
        is_default=False,
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


def update_prompt_metrics(db: Session, prompt_id: int, metrics: Dict) -> None:
    """Update performance metrics for a prompt version."""
    prompt = db.query(PromptVersion).filter(PromptVersion.id == prompt_id).first()
    if prompt:
        current = prompt.performance_metrics or {}
        current.update(metrics)
        prompt.performance_metrics = current
        db.commit()


def duplicate_prompt(db: Session, prompt_id: int, tenant_id: int, new_name: str) -> Optional[PromptVersion]:
    """Duplicate a prompt for customization."""
    source = db.query(PromptVersion).filter(PromptVersion.id == prompt_id).first()
    if not source:
        return None

    new_prompt = PromptVersion(
        tenant_id=tenant_id,
        version=f"{source.version}-custom",
        name=new_name,
        description=f"Customized from: {source.name}",
        system_prompt=source.system_prompt,
        context_template=source.context_template,
        task_template=source.task_template,
        model=source.model,
        temperature=source.temperature,
        max_tokens=source.max_tokens,
        is_active=False,
        is_default=False,
    )
    db.add(new_prompt)
    db.commit()
    db.refresh(new_prompt)
    return new_prompt
