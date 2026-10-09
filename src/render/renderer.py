"""Playwright-based HTML-to-PNG renderer for the Hassan Daily Infographic."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
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
        html_path = self.render_html(data)
        output_png_path = self.output_dir / output_filename
        
        # File URL for Playwright
        file_url = f"file://{html_path.resolve()}"

        with sync_playwright() as p:
            # Launch headless browser
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
            
            # Navigate to the rendered template
            page.goto(file_url, wait_until="networkidle")
            
            # Ensure web fonts (Cairo, Tajawal, Montserrat) are fully rendered
            page.evaluate("document.fonts.ready")
            
            # Small delay for final layout stabilization
            page.wait_for_timeout(400)
            
            # Capture full page screenshot
            page.screenshot(
                path=str(output_png_path),
                clip={"x": 0, "y": 0, "width": 1080, "height": 1350}
            )
            
            browser.close()

        return output_png_path
