from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.config import Settings, get_settings
from backend.schemas.schemas import CalcRequest, CalcResponse
from backend.services.agent import AIAnalystService
from backend.services.calc import CalcService
from backend.services.cpi import CPIDataError, CPIFetcherService

router = APIRouter()


def _cpi_service(settings: Settings = Depends(get_settings)) -> CPIFetcherService:
    return CPIFetcherService(settings)


def _calc_service() -> CalcService:
    return CalcService()


def _agent_service(settings: Settings = Depends(get_settings)) -> AIAnalystService:
    return AIAnalystService(settings)


@router.post("/calculate", response_model=CalcResponse)
async def calculate(
    req: CalcRequest,
    cpi_service: CPIFetcherService = Depends(_cpi_service),
    calc_service: CalcService = Depends(_calc_service),
    agent_service: AIAnalystService = Depends(_agent_service),
) -> CalcResponse:
    try:
        cpi_info = await cpi_service.get_cpi_for_prev_year(req.purchase_date)
    except CPIDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    calc = calc_service.calculate(
        request=req,
        cpi_index=cpi_info.cpi_index,
        index_factor=cpi_info.index_factor,
    )

    analysis_text: Optional[str] = None
    if req.with_analysis:
        try:
            analysis_text = agent_service.generate_analysis(
                property_type=req.property_type,
                cpi_index=cpi_info.cpi_index,
                index_factor=cpi_info.index_factor,
                calc=calc,
            )
        except Exception as exc:  # noqa: BLE001
            analysis_text = f"AI analysis unavailable: {exc}"

    return CalcResponse(
        **calc.model_dump(),
        cpi_index=cpi_info.cpi_index,
        cpi_year=cpi_info.year,
        cpi_month=cpi_info.month,
        index_factor=cpi_info.index_factor,
        analysis_text=analysis_text,
    )

