from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_decision_repository, get_event_repository, get_event_service
from src.api.schemas import DecisionDTO, DecisionResponse, EventDetailResponse, EventResponse, IngestResponse
from src.domain.event import DegradationEvent
from src.repositories.decision_repository import DecisionRepository
from src.repositories.event_repository import EventRepository
from src.services.event_service import EventIngestionService

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=IngestResponse)
async def ingest_event(payload: DegradationEvent, service: EventIngestionService = Depends(get_event_service)):
    result = service.ingest(payload)
    return IngestResponse(
        event_id=result.event_id,
        status=result.status,
        decision=DecisionDTO(
            action=result.decision.action.value,
            confidence=result.decision.confidence,
            reasoning=result.decision.reasoning,
            safe_to_auto=result.decision.safe_to_auto,
        ),
        approval_id=result.approval_id,
    )


@router.get("/", response_model=list[EventResponse])
async def list_events(repo: EventRepository = Depends(get_event_repository)):
    return repo.list()


@router.get("/{event_id}", response_model=EventDetailResponse)
async def get_event(
    event_id: str,
    event_repo: EventRepository = Depends(get_event_repository),
    decision_repo: DecisionRepository = Depends(get_decision_repository),
):
    event = event_repo.get(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    decision = decision_repo.get_by_event_id(event_id)
    data = EventResponse.model_validate(event).model_dump()
    data["decision"] = DecisionResponse.model_validate(decision) if decision else None
    return EventDetailResponse(**data)
