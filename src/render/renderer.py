"""Playwright-based HTML-to-PNG renderer for the Hassan Daily Infographic."""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

from ..config import settings


class InfographicRenderer:
    def __init__(self, templates_dir: Optional[Path] = None, output_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or settings.TEMPLATES_DIR
        self.output_dir = output_dir or settings.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )

    def render_html(self, data: Dict[str, Any], output_html_filename: str = "rendered_infographic.html") -> Path:
        """Renders the Jinja2 template with data context to an HTML file."""
        template = self.jinja_env.get_template("infographic.html")
        rendered_content = template.render(**data)
        
        output_html_path = self.templates_dir / output_html_filename
        with open(output_html_path, "w", encoding="utf-8") as f:
            f.write(rendered_content)
            
        return output_html_path

    def render_to_png(
        self,
        data: Dict[str, Any],
        output_filename: str = "daily_infographic.png",
        scale_factor: int = 1
    ) -> Path:
        """Renders HTML and captures a crisp 1080x1350 PNG using Playwright."""
        return self.render(data, output_filename, scale_factor)[0]

    def render(
        self,
        data: Dict[str, Any],
        output_filename: str = "daily_infographic.png",
        scale_factor: int = 1
    ) -> Tuple[Path, Dict[str, Any]]:
        """Renders the PNG and returns it with a report of what the page actually displayed.

        The report lists every [data-verify] element's text and position, plus overflowing boxes,
        broken images and unloaded fonts. src/safety/render_checks.py uses it to verify the image.
        """
        html_path = self.render_html(data)
        output_png_path = self.output_dir / output_filename

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu"
                ]
            )

            # Instagram portrait dimensions
            page = browser.new_page(
                viewport={"width": 1080, "height": 1350},
                device_scale_factor=scale_factor
            )
            page.goto(f"file://{html_path.resolve()}", wait_until="networkidle")
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(400)

            report = page.evaluate(PAGE_REPORT_JS)

            page.screenshot(
                path=str(output_png_path),
                clip={"x": 0, "y": 0, "width": 1080, "height": 1350}
            )
            browser.close()

        return output_png_path, report


PAGE_REPORT_JS = """
async () => {
  const W = 1080, H = 1350;
  const isClipped = (el) => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0 || r.left < 0 || r.top < 0 || r.right > W || r.bottom > H) return true;
    for (let a = el.parentElement; a; a = a.parentElement) {
      const st = getComputedStyle(a);
      if (st.overflow !== 'visible' || st.overflowX !== 'visible' || st.overflowY !== 'visible') {
        const ar = a.getBoundingClientRect();
        if (r.left < ar.left - 1 || r.top < ar.top - 1 || r.right > ar.right + 1 || r.bottom > ar.bottom + 1) return true;
      }
      if (st.visibility === 'hidden' || st.display === 'none' || st.opacity === '0') return true;
    }
    return false;
  };

  const items = [...document.querySelectorAll('[data-verify]')].map(el => {
    const r = el.getBoundingClientRect();
    return { key: el.dataset.verify, text: el.textContent.trim(), x: r.x, y: r.y, w: r.width, h: r.height, clipped: isClipped(el) };
  });

  const boxes = '.price-card, .card-body, .card-footer, .analysis-column, .bullets, .tip-box, .disclaimer, .header-branding';
  const overflowing = [...document.querySelectorAll(boxes)]
    .filter(el => el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1)
    .map(el => el.className);
  if (document.documentElement.scrollHeight > H + 1) overflowing.push('page taller than 1350px');

  const brokenImages = [...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.getAttribute('src'));
  const bgUrls = [...new Set([...document.querySelectorAll('*')]
    .map(e => getComputedStyle(e).backgroundImage)
    .filter(b => b.startsWith('url('))
    .map(b => b.slice(5, -2)))];
  for (const u of bgUrls) {
    await new Promise(res => { const i = new Image(); i.onload = res; i.onerror = () => { brokenImages.push(u); res(); }; i.src = u; });
  }

  const missingFonts = ['Cairo', 'Tajawal', 'Montserrat'].filter(f => !document.fonts.check(`700 20px "${f}"`));
  return { items, overflowing, brokenImages, missingFonts };
}
"""
