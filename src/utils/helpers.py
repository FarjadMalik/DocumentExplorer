from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_relative_path(filename: str) -> Path:
    """Get the relative path of the current file from the project root."""

    current_file = Path(filename).resolve()

    # Go up until you find your project root (e.g. contains .git or pyproject.toml)
    for parent in current_file.parents:
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            project_root = parent
            break
    else:
        project_root = current_file.parent  # fallback

    # relative_path = code_dir.relative_to(Path(__name__).resolve().parent)
    relative_path = current_file.relative_to(project_root)
    return relative_path

def write_to_markdown(summary, key_points, output_file='article_summary.md'):
    md_content = f"# Article Summary\n{summary}\n\n## Key Points\n"
    for point in key_points:
        md_content += f"- {point}\n"
    
    with open(output_file, 'w') as f:
        f.write(md_content)

def save_text(path: str, text: str) -> None:
    """Save scraped text to a local file."""
    file_path = Path(path)
    file_path.write_text(text, encoding="utf-8")
