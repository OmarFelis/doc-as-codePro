"""Doc-as-Code Service - Servicio moderno de documentación automática."""
import os

# Fix: IntelliJ + Amazon Q inyecta AWS_CONFIG_FILE apuntando a un tmp vacío
# y no propaga AWS_PROFILE al subproceso. Se leen del .env antes de boto3.
if not os.getenv("AWS_PROFILE") or not os.getenv("AWS_CONFIG_FILE") or ".tmp" in os.getenv("AWS_CONFIG_FILE", ""):
    import pathlib
    _env = pathlib.Path(__file__).parent.parent / ".env"
    if _env.exists():
        for _line in _env.read_text(encoding="utf-8").splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())
    # Fallback si AWS_CONFIG_FILE sigue siendo un tmp vacío
    _cfg = os.getenv("AWS_CONFIG_FILE", "")
    if not _cfg or "Temp" in _cfg or ".tmp" in _cfg:
        os.environ["AWS_CONFIG_FILE"] = os.path.join(os.path.expanduser("~"), ".aws", "config").replace("\\", "/")

__version__ = "3.0.0"
