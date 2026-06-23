from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_approval_repository, get_approval_service
from src.api.schemas import ApprovalActionRequest, ApprovalActionResponse, ApprovalResponse
from src.repositories.approval_repository import ApprovalRepository
from src.services.approval_service import ApprovalService
from src.services.exceptions import ApprovalAlreadyResolvedError, ApprovalNotFoundError

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("/", response_model=list[ApprovalResponse], summary="Listar approval requests pendientes")
async def list_approvals(repo: ApprovalRepository = Depends(get_approval_repository)):
    return repo.list_pending()


@router.post("/{approval_id}/approve", response_model=ApprovalActionResponse, summary="Aprobar y ejecutar una acción pendiente")
async def approve(
    approval_id: str,
    body: ApprovalActionRequest = ApprovalActionRequest(),
    service: ApprovalService = Depends(get_approval_service),
):
    try:
        result = service.approve(approval_id, body.feedback)
    except ApprovalNotFoundError:
        raise HTTPException(status_code=404, detail="Approval not found")
    except ApprovalAlreadyResolvedError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ApprovalActionResponse(approval_id=result.approval_id, status=result.status, result=result.result)


@router.post("/{approval_id}/reject", response_model=ApprovalActionResponse, summary="Rechazar una acción pendiente")
async def reject(
    approval_id: str,
    body: ApprovalActionRequest = ApprovalActionRequest(),
    service: ApprovalService = Depends(get_approval_service),
):
    try:
        result = service.reject(approval_id, body.feedback)
    except ApprovalNotFoundError:
        raise HTTPException(status_code=404, detail="Approval not found")
    except ApprovalAlreadyResolvedError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ApprovalActionResponse(approval_id=result.approval_id, status=result.status, result=result.result)
