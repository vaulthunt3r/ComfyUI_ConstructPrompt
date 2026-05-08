import random
import logging
from pathlib import Path
from functools import lru_cache
from typing import List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TAGS_DIR = Path(__file__).parent.resolve() / "tags"

PRELOAD_FILE_LIMIT = 3
PRELOAD_TAG_LIMIT_PER_FILE = 100


def _normalize_source_string(source: str) -> str:
    if not source or not isinstance(source, str):
        return ""
    return source.replace("📂", "").replace("📄", "").strip()


def _parse_source_string(source: str) -> Tuple[Optional[str], Optional[str]]:
    clean = _normalize_source_string(source)
    parts = [p.strip() for p in clean.split("/") if p.strip()]
    if len(parts) != 2:
        return None, None
    cat = parts[0]
    file = parts[1]
    if file.lower().endswith(".txt"):
        file = file[:-4]
    return cat, file


@lru_cache(maxsize=2048)
def _get_tags_from_file_path(cat: str, file: str) -> List[str]:
    path = TAGS_DIR / cat / f"{file}.txt"
    if not path.exists() or not path.is_file():
        logger.debug("Tags file not found: %s", path)
        return []
    tags: List[str] = []
    try:
        with path.open("r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                for t in line.split(","):
                    t = t.strip()
                    if t:
                        tags.append(t)
    except Exception as e:
        logger.error("Ошибка чтения %s: %s", path, e)
        return []
    seen = set()
    unique = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


@lru_cache(maxsize=2048)
def _get_raw_tag_lines_from_file_path(cat: str, file: str) -> List[str]:
    path = TAGS_DIR / cat / f"{file}.txt"
    if not path.exists() or not path.is_file():
        logger.debug("Tags file not found: %s", path)
        return []
    lines: List[str] = []
    try:
        with path.open("r", encoding="utf-8-sig") as f:
            for line in f:
                raw = line.rstrip("\n")
                stripped = raw.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                lines.append(raw)
    except Exception as e:
        logger.error("Ошибка чтения %s: %s", path, e)
        return []
    return lines


class ConstructPrompt:
    @classmethod
    def INPUT_TYPES(cls):
        categories = []
        if TAGS_DIR.exists() and TAGS_DIR.is_dir():
            categories = sorted([d.name for d in TAGS_DIR.iterdir() if d.is_dir()])
        logger.info("[ConstructPrompt] Found categories: %s", categories)

        if not categories:
            return {"required": {"source": ([""], {"default": ""}), "tag": ([""], {"default": ""})}}

        sources = []
        for cat in categories:
            cat_path = TAGS_DIR / cat
            for f in sorted(cat_path.glob("*.txt")):
                if f.is_file():
                    sources.append(f"📂 {cat} / {f.stem}")

        default_src = sources[0] if sources else ""

        # Убрали предзагрузку тегов: оставляем только основные опции без добавленных tag_options из файлов
        tag_options = ["🚫 None", "🎲 Random", "✏️ Manual", "🔎 Show tags for selected file (multiline)"]

        return {
            "required": {
                "source": (sources, {
                    "default": default_src,
                    "tooltip": "Выбери путь: 📂 Папка / 📄 Файл\n(Теги можно показать отдельно через опцию Show tags)"
                }),
                "tag": (tag_options, {
                    "default": "🎲 Random",
                    "tooltip": "None, Random, Manual, Show tags (multiline)"
                }),
                "tag_text": ("STRING", {"default": "", "tooltip": "Если выбрали Manual — введите тег здесь"}),
                "delimiter": ("STRING", {"default": ", "}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }

    @classmethod
    def IS_CHANGED(cls, source, tag, tag_text, delimiter, seed):
        _get_tags_from_file_path.cache_clear()
        _get_raw_tag_lines_from_file_path.cache_clear()
        return hash(f"{source}|{tag}|{tag_text}|{delimiter}|{seed}")

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "execute"
    CATEGORY = "prompt"

    def execute(self, source: str, tag: str, tag_text: str, delimiter: str, seed) -> Tuple[str]:
        try:
            seed = int(seed) if seed is not None else 0
        except (ValueError, TypeError):
            seed = 0
        if not isinstance(delimiter, str) or delimiter == "":
            delimiter = ", "

        logger.debug("[ConstructPrompt.execute] source=%r tag=%r tag_text=%r seed=%r", source, tag, tag_text, seed)

        if not source:
            return ("",)

        if isinstance(tag, str) and tag.startswith("🔎 Show tags for selected file"):
            cat, file = _parse_source_string(source)
            if not cat:
                return ("",)
            raw_lines = _get_raw_tag_lines_from_file_path(cat, file)
            return ("\n".join(raw_lines) if raw_lines else "",)

        if isinstance(tag, str) and " || " in tag:
            src_part, real_tag = tag.split(" || ", 1)
            if src_part != source:
                logger.warning("tag source %r != selected source %r", src_part, source)
            return (real_tag,)

        if tag in ("🎲 Random", "Random"):
            cat, file = _parse_source_string(source)
            if not cat:
                return ("",)
            tags = _get_tags_from_file_path(cat, file)
            if not tags:
                return ("",)
            rng = random.Random(seed)
            return (rng.choice(tags),)

        if tag in ("✏️ Manual", "Manual"):
            return (str(tag_text).strip(),)

        if tag in ("🚫 None", "None", ""):
            return ("",)

        return (str(tag),)


NODE_CLASS_MAPPINGS = {"ConstructPrompt": ConstructPrompt}
NODE_DISPLAY_NAME_MAPPINGS = {"ConstructPrompt": "🏗️ Construct Prompt"}
