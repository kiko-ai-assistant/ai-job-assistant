import os
from pathlib import Path
from dotenv import load_dotenv

from src.utils.exceptions import EnvVarMissingError

APP_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]

# Load .env from app dir first, then fallback to repo root
load_dotenv(APP_DIR / ".env")
load_dotenv(REPO_ROOT / ".env")

# --- Data filepaths ---
BASE_DIR = REPO_ROOT
DATA_DIR = BASE_DIR / os.getenv("DATA_DIR", "data")

MEDIA_DIR = DATA_DIR / os.getenv("MEDIA_DIR", "media")
LOGS_DIR = DATA_DIR / os.getenv("LOGS_DIR", "logs")

MIGRATIONS_DIR = BASE_DIR / os.getenv("MIGRATIONS_DIR", "database/migrations")
SQL_DIR = MIGRATIONS_DIR

CVS_DIR = DATA_DIR / os.getenv("CVS_DIR", "cvs")

MEDIA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
CVS_DIR.mkdir(parents=True, exist_ok=True)

# --- Database configuration
def load_db_config() -> str:
    """Loads database config from environment's variables and returns connection uri"""
    host = os.getenv("DB_HOST")
    if not host:
        raise EnvVarMissingError("DB_HOST")

    port = os.getenv("DB_PORT", 5432)

    user = os.getenv("DB_USER")
    if not user:
        raise EnvVarMissingError("DB_USER")

    password = os.getenv("DB_PASSWORD")
    if not password:
        raise EnvVarMissingError("DB_PASSWORD")

    db_name = os.getenv("DB_NAME")
    if not db_name:
        raise EnvVarMissingError("DB_NAME")

    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

def load_db_test_config() -> str:
    """Loads test database config from environment's variables and returns connection uri"""
    host = os.getenv("TEST_DB_HOST")
    if not host:
        raise EnvVarMissingError("TEST_DB_HOST")

    port = os.getenv("TEST_DB_PORT")
    if not port:
        raise EnvVarMissingError("TEST_DB_PORT")

    user = os.getenv("TEST_DB_USER")
    if not user:
        raise EnvVarMissingError("TEST_DB_USER")

    password = os.getenv("TEST_DB_PASSWORD")
    if not password:
        raise EnvVarMissingError("TEST_DB_PASSWORD")

    db_name = os.getenv("TEST_DB_NAME")
    if not db_name:
        raise EnvVarMissingError("TEST_DB_NAME")

    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


# --- Media paths ---
WELCOME_VIDEO = MEDIA_DIR / "welcome.mp4"
WELCOME_VIDEO_FID = "BAACAgIAAxkBAAMUabJHwGPAr0xFl7vPUNP3KYAu0WUAAmeLAAIiaJlJsyvuJcpMVTU6BA"

# --- Bot's configuration ---
BOT_TOKEN = os.getenv("BOT_TOKEN")

DEFAULT_LANGUAGE = "en"

# Programming Languages
LANGUAGES = [
    "Python", "JavaScript", "TypeScript", "Go",
    "Rust", "Java", "C#", "C++", "Ruby"
    "Swift", "Kotlin", "PHP", "Dart"
]

COMMON_SKILLS = [
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "ClickHouse",
    "Docker", "Kubernetes", "Nginx", "Terraform", "Ansible", "CI/CD", "Linux",
    "REST", "gRPC", "GraphQL", "WebSocket",
    "RabbitMQ", "Apache Kafka",
    "AWS", "Google Cloud", "Azure"
]

SKILLS_TREE = {
    "Python": [
        "FastAPI", "REST", "PyTorch", "TensorFlow", "LangChain", "LlamaIndex",
        "Pandas", "NumPy", "Scikit-learn", "HuggingFace", "Diffusers",
        "SQLAlchemy", "Pytest", "Django", "Celery", "ONNX"
    ],
    "Rust": [
        "Axum", "Tokio", "Tauri", "WASM",
        "Serde", "Rocket", "Polars", "Actix", "Docker"
    ],
    "JavaScript": [
        "React", "Vue.js", "Next.js", "Vite",
        "Express.js", "Three.js", "WebGPU"
    ],
    "TypeScript": [
        "NestJS", "Prisma", "Zod", "Deno",
        "Bun", "TRPC", "SvelteKit", "Effect"
    ],
    "Go": [
        "Gin", "Echo", "Protobuf", "gRPC", "golang-migrate",
        "Gorm", "Docker", "PostgreSQL", "Kafka"
    ],
    "Java": [
        "Spring Boot", "Quarkus", "Micronaut",
        "Hibernate", "Maven", "Loom"
    ],
    "C++": [
        "STL", "Boost", "Qt", "CMake", "GDB",
        "C++23", "CUDA", "OpenCV",
        "Unreal Engine", "Embedded", "Docker"
    ],
    "C#": [
        ".NET", "Entity Framework", "ASP.NET Core",
        "Unity", "Blazor", "Maui"
    ],
    "Ruby": [
        "Ruby on Rails", "Sidekiq", "RSpec",
        "Hanami", "Sorbet", "Capistrano",
        "PostgreSQL", "Redis", "Docker"
    ],
    "Dart": [
        "Flutter", "Riverpod", "Bloc", "GetX",
        "Dio", "Isolates", "Dart Frog (Server)",
        "Shorebird (Code Push)", "Firebase", "SQLite"
    ],
    "Kotlin": [
        "KMP (Multiplatform)", "Compose",
        "Coroutines", "Ktor", "Android SDK"
    ],
    "Swift": [
        "SwiftUI", "Combine",
        "Async/Await", "Vapor", "iOS SDK"
    ],
    "PHP": [
        "Laravel", "Symfony", "Composer",
        "Docker", "MySQL"
    ],
}
