from typing import Dict, Any

class CanvasArtifactEngine:
    """
    Renders and manages interactive Canvas Artifacts (HTML, SVG, Python, React).
    Generates structured artifact payloads compatible with Nox Mobile & Web Canvas Modals.
    """

    @staticmethod
    def create_artifact(title: str, language: str, content: str) -> Dict[str, Any]:
        return {
            "type": "canvas_artifact",
            "title": title,
            "language": language.lower(),
            "code": content.strip(),
            "can_preview": language.lower() in ["html", "svg", "jsx", "tsx", "markdown"],
            "can_execute": language.lower() in ["python", "javascript", "typescript", "bash"]
        }
