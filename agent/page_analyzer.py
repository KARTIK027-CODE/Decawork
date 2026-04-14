from playwright.async_api import Page
from typing import Dict, Any, List
from config.logger import logger

class PageAnalyzer:
    """
    Responsibilities:
    Extract structured context: visible text, buttons, forms, links.
    Simplify the DOM into an LLM-friendly schema for robust decision-making.
    """
    
    @staticmethod
    async def get_snapshot(page: Page) -> Dict[str, Any]:
        """Runs Javascript inside the browser to extract a semantic, simplified view of the UI."""
        logger.info("Extracting semantic UI snapshot from frame")
        
        # We inject a script into the page to extract only relevant interactive and text elements.
        extract_script = """
        () => {
            const getVisibleText = (el) => {
                let rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) return null;
                return el.innerText ? el.innerText.trim() : null;
            };
            
            const interactables = [];
            document.querySelectorAll('button, a, input, select, textarea, tr').forEach(el => {
                let visibleText = getVisibleText(el);
                let tag = el.tagName.toLowerCase();
                let info = {
                    tag: tag,
                    text: visibleText || '',
                };
                
                if (['input', 'textarea', 'select'].includes(tag)) {
                    info.name = el.name || '';
                    info.type = el.type || '';
                    info.placeholder = el.placeholder || '';
                    info.value = el.value || '';
                }
                
                if (tag === 'a') {
                    info.href = el.getAttribute('href') || '';
                }
                
                if (info.text || ['input', 'select', 'textarea'].includes(tag)) {
                    interactables.push(info);
                }
            });
            
            return {
                title: document.title,
                url: window.location.href,
                elements: interactables
            };
        }
        """
        try:
            snapshot = await page.evaluate(extract_script)
            logger.info("Snapshot extracted successfully", extra={"context": {"element_count": len(snapshot.get("elements", []))}})
            return snapshot
        except Exception as e:
            logger.error(f"Failed to extract page snapshot: {e}")
            return {"title": "", "url": page.url, "elements": [], "error": str(e)}

    @staticmethod
    def simplify_for_llm(snapshot: Dict[str, Any]) -> str:
        """Converts the JSON snapshot into a highly compact text block for LLM context."""
        lines = []
        lines.append(f"PAGE TITLE: {snapshot.get('title')}")
        lines.append(f"CURRENT URL: {snapshot.get('url')}")
        lines.append("INTERACTABLE ELEMENTS:")
        
        for el in snapshot.get('elements', []):
            desc = f"[{el['tag'].upper()}]"
            if el.get('name'):
                desc += f" name='{el['name']}'"
            if el.get('type'):
                desc += f" type='{el['type']}'"
            if el.get('text'):
                desc += f" text='{el['text']}'"
            if el.get('placeholder'):
                desc += f" placeholder='{el['placeholder']}'"
            
            lines.append(desc)
            
        return "\\n".join(lines)
