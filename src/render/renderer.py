"""Playwright-based HTML-to-PNG renderer for the Hassan Daily Infographic."""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

from ..config import settings


# Feed posts: 4:5 portrait (Facebook and Instagram). Stories: 9:16.
WIDTH = 1080
FEED_HEIGHT = 1350
STORY_HEIGHT = 1920


class InfographicRenderer:
    def __init__(self, templates_dir: Optional[Path] = None, output_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or settings.TEMPLATES_DIR
        self.output_dir = output_dir or settings.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )

    def render_html(self, data: Dict[str, Any], output_html_filename: str = "rendered_infographic.html",
                    template_name: str = "infographic.html") -> Path:
        """Renders the Jinja2 template with data context to an HTML file."""
        template = self.jinja_env.get_template(template_name)
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
        scale_factor: int = 1,
        template_name: str = "infographic.html",
        height: int = FEED_HEIGHT,
    ) -> Tuple[Path, Dict[str, Any]]:
        """Renders the PNG and returns it with a report of what the page actually displayed.

        The report lists every [data-verify] element's text and position, plus overflowing boxes,
        broken images and unloaded fonts. src/safety/render_checks.py uses it to verify the image.
        """
        html_path = self.render_html(data, f"rendered_{Path(template_name).stem}.html", template_name)
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

            page = browser.new_page(
                viewport={"width": WIDTH, "height": height},
                device_scale_factor=scale_factor
            )
            page.goto(f"file://{html_path.resolve()}", wait_until="networkidle")
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(400)

            page.evaluate(FIT_TEXT_JS)
            report = page.evaluate(PAGE_REPORT_JS, [WIDTH, height])

            page.screenshot(
                path=str(output_png_path),
                clip={"x": 0, "y": 0, "width": WIDTH, "height": height}
            )
            browser.close()

        return output_png_path, report

    def render_story(self, data: Dict[str, Any], output_filename: str = "daily_story.png") -> Tuple[Path, Dict[str, Any]]:
        """Renders the 1080x1920 story (the four prices in large type), with the same page report."""
        return self.render(data, output_filename, template_name="story.html", height=STORY_HEIGHT)



# Long AI text on a given day: shrink that section's text in small steps until it fits,
# never below the minimum. The page report's overflow check is still the final guard.
FIT_TEXT_JS = """
() => {
  const fit = (boxSel, textSel, minPx) => {
    for (const box of document.querySelectorAll(boxSel)) {
      const texts = [...box.querySelectorAll(textSel)];
      for (let i = 0; i < 40 && box.scrollHeight > box.clientHeight + 1; i++) {
        let shrunk = false;
        for (const t of texts) {
          const size = parseFloat(getComputedStyle(t).fontSize);
          if (size - 0.5 >= minPx) { t.style.fontSize = (size - 0.5) + 'px'; shrunk = true; }
        }
        if (!shrunk) break;
      }
    }
  };
  fit('.analysis-column', '.bullet-content', 21);
  fit('.tip-box', '.tip-body', 18);
}
"""

PAGE_REPORT_JS = """
async ([W, H]) => {
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

  const boxes = '.price-card, .card-body, .card-footer, .analysis-column, .bullets, .tip-box, .disclaimer, .header-branding, .s-card, .s-body, .s-footer';
  const overflowing = [...document.querySelectorAll(boxes)]
    .filter(el => el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1)
    .map(el => el.className);
  if (document.documentElement.scrollHeight > H + 1) overflowing.push(`page taller than ${H}px`);

  const brokenImages = [...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.getAttribute('src'));
  const bgUrls = [...new Set([...document.querySelectorAll('*')]
    .map(e => getComputedStyle(e).backgroundImage)
    .filter(b => b.startsWith('url('))
    .map(b => b.slice(5, -2)))];
  for (const u of bgUrls) {
    await new Promise(res => { const i = new Image(); i.onload = res; i.onerror = () => { brokenImages.push(u); res(); }; i.src = u; });
  }

  const missingFonts = ['IBM Plex Sans Arabic', 'Montserrat'].filter(f => !document.fonts.check(`700 20px "${f}"`));
  return { items, overflowing, brokenImages, missingFonts };
}
"""
