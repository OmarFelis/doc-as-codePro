"""README generator using AI."""

from typing import Dict, List
from src.core.generators.base import DocumentationGenerator
from src.core.llm.base import LLMClient
from src.models.domain import ProjectAnalysis, FileAnalysis, ComponentType
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ReadmeGenerator(DocumentationGenerator):
    """Generates README.md files automatically using AI."""

    def __init__(self, llm_client: LLMClient):
        """
        Initialize README generator.

        Args:
            llm_client: LLM client to use for generation
        """
        self.llm = llm_client

    async def generate(self, analysis: ProjectAnalysis) -> str:
        """Generate README.md from project analysis."""
        if not self.llm.is_available():
            logger.warning("llm_not_available", message="Falling back to template")
            return self._generate_template_readme(analysis)

        try:
            prompt = self._build_prompt(analysis)
            readme_content = await self.llm.generate_text(
                prompt=prompt,
                max_tokens=3000,
                temperature=0.7,
                system_prompt="You are an expert technical writer creating professional README documentation.",
            )
            
            logger.info("readme_generated", repository=analysis.repository_name)
            return readme_content

        except Exception as e:
            logger.error("readme_generation_failed", error=str(e))
            return self._generate_template_readme(analysis)

    def _build_prompt(self, analysis: ProjectAnalysis) -> str:
        """Build prompt for LLM."""
        # Summarize components
        component_summary = self._format_components(analysis.components)
        
        # Get main files
        main_files = self._get_main_files(analysis.files)
        
        # Detect frameworks/libraries
        frameworks = self._detect_frameworks(analysis.files)

        prompt = f"""Generate a professional README.md for the following software project:

**Project Name:** {analysis.repository_name}
**Owner:** {analysis.repository_owner}
**Languages:** {', '.join([str(lang) for lang in analysis.languages])}
**Total Files:** {analysis.total_files}
**Total Lines of Code:** {analysis.total_lines}

**Component Breakdown:**
{component_summary}

**Main Files:**
{main_files}

**Detected Frameworks/Libraries:**
{frameworks}

Generate a comprehensive README that includes:
1. **Project Title** with appropriate emoji
2. **Description** - What the project does and its purpose
3. **Features** - Key features/capabilities (bullet points)
4. **Tech Stack** - Technologies used
5. **Project Structure** - Brief overview of directory structure
6. **Getting Started** - Installation and setup instructions
7. **Usage** - Basic usage examples
8. **Contributing** (optional) - Brief contribution guidelines if applicable
9. **License** (optional) - Mention if detectable

Use professional markdown formatting with appropriate emojis. Make it engaging and informative."""

        return prompt

    def _format_components(self, components: Dict[ComponentType, List[str]]) -> str:
        """Format component breakdown."""
        result = []
        for comp_type, files in components.items():
            if files:
                result.append(f"- **{comp_type.value.upper()}**: {len(files)} files")
        return "\n".join(result) if result else "- No components classified"

    def _get_main_files(self, files: List[FileAnalysis], max_files: int = 5) -> str:
        """Get list of main files."""
        # Sort by lines of code (larger files first)
        sorted_files = sorted(files, key=lambda f: f.lines, reverse=True)[:max_files]
        
        result = []
        for file in sorted_files:
            result.append(f"- `{file.file_path}` ({file.language}, {file.lines} lines)")
        
        return "\n".join(result) if result else "- No files analyzed"

    def _detect_frameworks(self, files: List[FileAnalysis]) -> str:
        """Detect frameworks from imports."""
        frameworks = set()
        
        for file in files:
            for imp in file.imports:
                # Common frameworks
                if any(fw in imp.lower() for fw in ["django", "flask", "fastapi"]):
                    frameworks.add("Python Web Framework")
                elif any(fw in imp.lower() for fw in ["spring", "springboot"]):
                    frameworks.add("Spring Boot")
                elif any(fw in imp.lower() for fw in ["express", "nestjs"]):
                    frameworks.add("Node.js Web Framework")
                elif any(fw in imp.lower() for fw in ["react", "angular", "vue"]):
                    frameworks.add("Frontend Framework")
                elif any(fw in imp.lower() for fw in ["sqlalchemy", "hibernate", "prisma"]):
                    frameworks.add("ORM")

        return "\n".join(f"- {fw}" for fw in sorted(frameworks)) if frameworks else "- No major frameworks detected"

    def _generate_template_readme(self, analysis: ProjectAnalysis) -> str:
        """Generate a template README when LLM is not available."""
        template = f"""# {analysis.repository_name}

## 📊 Project Overview

This project contains {analysis.total_files} files with approximately {analysis.total_lines:,} lines of code.

### Languages
{', '.join([str(lang) for lang in analysis.languages])}

### Component Breakdown
{self._format_components(analysis.components)}

## 🚀 Getting Started

### Prerequisites
- Ensure you have the necessary runtime for the detected languages

### Installation
```bash
# Clone the repository
git clone https://github.com/{analysis.repository_owner}/{analysis.repository_name}.git

#  Change to project directory
cd {analysis.repository_name}

# Install dependencies
# (depends on your project type)
```

## 📁 Project Structure

```
{analysis.repository_name}/
├── ... (main files and directories)
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

Please check the repository for license information.

---

*This README was generated automatically by doc-as-code service.*
"""
        return template
