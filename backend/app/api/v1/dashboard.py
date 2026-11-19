from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import authenticate_request as get_current_user
from app.models.auth import AuthenticatedUser
from app.services.cache import get_revenue_summary
from app.services.reservations import UnsupportedRevenueCurrency, list_properties

router = APIRouter()


@router.get("/dashboard/properties")
async def get_dashboard_properties(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
):
    return await list_properties(current_user.tenant_id)


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    year: Annotated[int | None, Query(ge=1, le=9998)] = None,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
):
    if month is not None and year is None:
        raise HTTPException(status_code=422, detail="A year is required when filtering by month")

    try:
        revenue = await get_revenue_summary(property_id, current_user.tenant_id, year, month)
    except UnsupportedRevenueCurrency as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if revenue is None:
        raise HTTPException(status_code=404, detail="Property not found")

    return {
        "property_id": revenue["property_id"],
        "total_revenue": float(revenue["total"]),
        "currency": revenue["currency"],
        "reservations_count": revenue["count"],
    }
