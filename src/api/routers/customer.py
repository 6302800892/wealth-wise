"""Customer controllers (/me/*): risk profile, goals and recommendations. CUSTOMER role only (NFR-04)."""

from fastapi import APIRouter, Depends, Response

from src.api.deps import customer_user, get_ctx
from src.api.schemas import AssessmentRequest, GoalCreateRequest, GoalUpdateRequest, RecommendationRequest
from src.service import goal_service, recommendation_service, risk_profile_service
from src.service.context import ServiceContext
from src.types.identity import AuthUser

router = APIRouter(prefix="/me", tags=["customer"], dependencies=[Depends(customer_user)])
questionnaire_router = APIRouter(tags=["customer"], dependencies=[Depends(customer_user)])


@questionnaire_router.get("/questionnaire")
def get_questionnaire(ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return risk_profile_service.questionnaire(ctx)


@router.post("/risk-assessments", status_code=201)
def submit_assessment(body: AssessmentRequest, user: AuthUser = Depends(customer_user),
                      ctx: ServiceContext = Depends(get_ctx)) -> dict:
    answers = [(a.question_id, a.option_id) for a in body.answers]
    return risk_profile_service.submit_assessment(ctx, user, body.rule_set_version, answers)


@router.get("/risk-profile")
def get_risk_profile(user: AuthUser = Depends(customer_user), ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return risk_profile_service.risk_profile(ctx, user.customer_id)


@router.post("/goals", status_code=201)
def create_goal(body: GoalCreateRequest, user: AuthUser = Depends(customer_user),
                ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return goal_service.create_goal(
        ctx, user.customer_id, name=body.name, goal_type=body.goal_type, target_amount=body.target_amount,
        target_date=body.target_date, priority=body.priority,
    )


@router.get("/goals")
def list_goals(user: AuthUser = Depends(customer_user), ctx: ServiceContext = Depends(get_ctx)) -> dict:
    items = goal_service.list_goals(ctx, user.customer_id)
    return {"items": items, "next_cursor": None, "total": len(items)}


@router.get("/goals/{goal_id}")
def get_goal(goal_id: str, user: AuthUser = Depends(customer_user), ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return goal_service.get_goal(ctx, user.customer_id, goal_id)


@router.patch("/goals/{goal_id}")
def update_goal(goal_id: str, body: GoalUpdateRequest, user: AuthUser = Depends(customer_user),
                ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return goal_service.update_goal(ctx, user.customer_id, goal_id, body.model_dump(exclude_unset=True))


@router.post("/recommendations")
def create_recommendation(response: Response, body: RecommendationRequest | None = None,
                          user: AuthUser = Depends(customer_user), ctx: ServiceContext = Depends(get_ctx)) -> dict:
    view, created = recommendation_service.generate(ctx, user.customer_id, body.goal_id if body else None)
    response.status_code = 201 if created else 200
    return view


@router.get("/recommendations/latest")
def latest_recommendation(user: AuthUser = Depends(customer_user), ctx: ServiceContext = Depends(get_ctx)) -> dict:
    return recommendation_service.latest(ctx, user.customer_id)
