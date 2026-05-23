"""POST /api/scrape — 爬取 URL"""
from fastapi import APIRouter
from schemas import ScrapeRequest, ScrapeResponse
from services.scraper import scrape_url

router = APIRouter()


@router.post("/api/scrape", response_model=ScrapeResponse)
async def scrape(req: ScrapeRequest) -> ScrapeResponse:
    """爬取视频链接，返回视频列表"""
    return await scrape_url(req.url)
