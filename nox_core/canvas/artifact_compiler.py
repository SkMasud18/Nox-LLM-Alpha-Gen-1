"""
Nox Canvas Artifact Compiler & Sandbox Engine
Author: Sk Masud Rahaman (@SkMasud18) - Falcon Intelligence
Compiles generated code, SVG visualizations, and interactive widgets into secure sandboxed payloads.
"""

from typing import Dict, Any, List

class ArtifactCompiler:
    SUPPORTED_LANGUAGES = ["html", "svg", "react", "python", "javascript", "mermaid"]

    @classmethod
    def compile_payload(cls, title: str, language: str, code: str) -> Dict[str, Any]:
        normalized_lang = language.lower().strip()
        if normalized_lang not in cls.SUPPORTED_LANGUAGES:
            normalized_lang = "markdown"

        return {
            "version": "2.0",
            "metadata": {
                "title": title,
                "language": normalized_lang,
                "sandbox_isolation": "strict-origin",
                "interactive": normalized_lang in ["html", "svg", "react", "javascript"]
            },
            "payload": {
                "source": code.strip(),
                "rendered_preview_available": True
            }
        }
