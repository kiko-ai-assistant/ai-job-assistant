import os
from pathlib import Path
from src.config import CVS_DIR

def cv_is_correct(filename: str, mimetype: str) -> bool:
    allowed_extensions = ('.pdf', '.docx', '.doc', '.txt')
    allowed_mimes = (
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
        'application/msword',  # .doc
        'text/plain'  # .txt
    )
    return filename.endswith(allowed_extensions) or mimetype in allowed_mimes


def get_cv_path(user_id: int, filename: str) -> Path:
    dir_path = CVS_DIR / str(user_id)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path / filename

def delete_cv(cv_path: Path | str) -> None:
    return os.remove(path=cv_path)
