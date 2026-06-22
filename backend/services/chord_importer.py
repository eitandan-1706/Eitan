from pathlib import Path


async def pdf_to_pngs(pdf_path: str, output_dir: str) -> list[str]:
    from pdf2image import convert_from_path
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    stem = Path(pdf_path).stem
    paths = []
    for i, page in enumerate(convert_from_path(pdf_path, dpi=150)):
        out = str(Path(output_dir) / f"{stem}_page{i+1}.png")
        page.save(out, "PNG")
        paths.append(out)
    return paths


async def screenshot_url(url: str, output_path: str) -> str:
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1200, "height": 900})
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.screenshot(path=output_path, full_page=True)
        await browser.close()
    return output_path
