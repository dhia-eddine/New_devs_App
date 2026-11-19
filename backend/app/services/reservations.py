from datetime import datetime

from sqlalchemy import text

from app.core.database_pool import db_pool


class UnsupportedRevenueCurrency(ValueError):
    pass


async def list_properties(tenant_id: str | None):
    async with db_pool.get_session() as session:
        result = await session.execute(
            text("SELECT id, name FROM properties WHERE tenant_id = :tenant_id ORDER BY name, id"),
            {"tenant_id": tenant_id},
        )
        return [dict(row) for row in result.mappings()]


async def calculate_total_revenue(
    property_id: str,
    tenant_id: str | None,
    year: int | None = None,
    month: int | None = None,
):
    params = {"property_id": property_id, "tenant_id": tenant_id}
    date_filter = ""
    if year is not None:
        end_year, end_month = (year + 1, 1) if month in (None, 12) else (year, month + 1)
        params.update(start_date=datetime(year, month or 1, 1), end_date=datetime(end_year, end_month, 1))
        date_filter = """
            AND r.check_in_date >= (CAST(:start_date AS timestamp) AT TIME ZONE p.timezone)
            AND r.check_in_date < (CAST(:end_date AS timestamp) AT TIME ZONE p.timezone)
        """

    query = text(f"""
        SELECT ROUND(COALESCE(SUM(r.total_amount), 0), 2) AS total,
               COUNT(r.id) AS count, r.currency
        FROM properties p
        LEFT JOIN reservations r ON r.property_id = p.id AND r.tenant_id = p.tenant_id
            {date_filter}
        WHERE p.id = :property_id AND p.tenant_id = :tenant_id
        GROUP BY r.currency
    """)
    async with db_pool.get_session() as session:
        result = await session.execute(query, params)
        rows = result.mappings().all()
    if not rows:
        return None
    summary = rows[0]
    if len(rows) > 1 or (summary["count"] and not summary["currency"]):
        raise UnsupportedRevenueCurrency("Revenue requires a single known currency per report")
    return {
        "property_id": property_id,
        "total": str(summary["total"]),
        "currency": summary["currency"] or "USD",
        "count": summary["count"], 
        
    }
