import hashlib
import json
import os
import re
import threading
from pathlib import Path
from typing import Dict, List, Optional

import torch
from diffusers import AutoPipelineForText2Image, DEISMultistepScheduler, DiffusionPipeline, LCMScheduler
from PIL import Image


SUPPORTED_IMAGE_MODELS: Dict[str, Dict[str, object]] = {
    "lcm-dreamshaper-v7": {
        "id": "SimianLuo/LCM_Dreamshaper_v7",
        "label": "LCM Dreamshaper v7",
        "width": 640,
        "height": 640,
        "steps": 6,
        "guidance_scale": 7.5,
        "scheduler": "lcm",
        "loader": "diffusion",
        "lcm_origin_steps": 50,
    },
    "dreamshaper-8-lcm": {
        "id": "Lykon/dreamshaper-8-lcm",
        "label": "DreamShaper 8 LCM",
        "width": 768,
        "height": 768,
        "steps": 10,
        "guidance_scale": 2.0,
        "scheduler": "lcm",
    },
    "dreamshaper-8": {
        "id": "Lykon/dreamshaper-8",
        "label": "DreamShaper 8",
        "width": 768,
        "height": 768,
        "steps": 20,
        "guidance_scale": 7.0,
        "scheduler": "deis",
    },
    "sd15": {
        "id": "stable-diffusion-v1-5/stable-diffusion-v1-5",
        "label": "Stable Diffusion v1.5",
        "width": 768,
        "height": 768,
        "steps": 24,
        "guidance_scale": 7.0,
    },
    "tiny-sd": {
        "id": "segmind/tiny-sd",
        "label": "Segmind Tiny SD",
        "width": 512,
        "height": 512,
        "steps": 14,
        "guidance_scale": 7.0,
    },
}

DEFAULT_MODEL_KEY = os.getenv("VENTUREOS_IMAGE_MODEL", "lcm-dreamshaper-v7").strip() or "lcm-dreamshaper-v7"
MAX_GENERATED_SLIDE_IMAGES = int(os.getenv("VENTUREOS_MAX_SLIDE_IMAGES", "5"))
DEFAULT_IMAGE_STYLE = os.getenv("VENTUREOS_IMAGE_STYLE", "deck-illustration").strip() or "deck-illustration"
DEFAULT_IMAGE_COVERAGE = os.getenv("VENTUREOS_IMAGE_COVERAGE", "key-slides").strip() or "key-slides"
DEFAULT_NEGATIVE_PROMPT = (
    "low quality, blurry, distorted, extra limbs, duplicate objects, bad anatomy, "
    "text, watermark, logo, cluttered composition, cropped subject, photorealistic, realistic photo, "
    "stock photo, portrait photo, realistic person, realistic people, realistic human face, selfie, live action, documentary, realistic skin, "
    "camera lens, professional photography"
)

IMAGE_STYLE_PRESETS: Dict[str, Dict[str, str]] = {
    "auto": {
        "label": "Storyboard",
        "prompt": "stylized scenic illustration, premium keynote artwork, cinematic atmosphere, clean composition, non-photoreal",
    },
    "deck-illustration": {
        "label": "Presentation Illustration",
        "prompt": "domain-specific editorial illustration, polished vector and 3D hybrid artwork, presentation-grade concept scene, premium dark-deck visual, non-photoreal",
    },
    "animated-scene": {
        "label": "Animated Scene",
        "prompt": "animated cinematic scene, stylized environment art, polished non-photoreal illustration, premium presentation artwork",
    },
    "illustration": {
        "label": "Editorial Illustration",
        "prompt": "premium editorial illustration, polished digital art, clean shapes, stylized scenic composition, non-photoreal",
    },
    "cartoon": {
        "label": "Cartoon",
        "prompt": "premium cartoon illustration, stylized scene, playful but polished, presentation-safe, non-photoreal artwork",
    },
    "product-mockup": {
        "label": "Product Illustration",
        "prompt": "product illustration, stylized device scene, polished UI on abstract surfaces, non-photoreal startup visual",
    },
    "3d-render": {
        "label": "3D Illustration",
        "prompt": "premium stylized 3D illustration, refined materials, scenic composition, non-photoreal keynote visual",
    },
    "abstract": {
        "label": "Abstract Scenic",
        "prompt": "abstract scenic artwork, atmospheric composition, gradient light, stylized environment, high-end keynote background",
    },
}

IMAGE_COVERAGE_OPTIONS: Dict[str, Dict[str, object]] = {
    "hero-only": {"label": "Hero Only (Fast)", "limit": 2},
    "key-slides": {"label": "Key Slides", "limit": 5},
    "image-heavy": {"label": "Image Heavy", "limit": 7},
    "all": {"label": "Every Slide", "limit": None},
}

SLIDE_IMAGE_DIRECTIVES: Dict[str, str] = {
    "hook": "hero concept illustration with a single strong focal scene, premium keynote composition, dark editorial mood",
    "problem": "contextual illustration showing system friction through interfaces, objects, or environment, not portrait photography",
    "stakes": "conceptual market-scale visual, domain-relevant scene, premium storytelling backdrop",
    "solution": "product-world illustration, polished interface-rich concept scene, modern and non-photoreal",
    "how_it_works": "diagrammatic workflow scene, structured composition, product and system storytelling",
    "impact": "outcome-driven editorial illustration, data-storytelling mood, premium executive presentation style",
    "proof": "credible proof visual through dashboards, model outputs, objects, charts, or environments, not realistic portraits",
    "business_model": "commercial system illustration using interfaces, objects, and contextual environment",
    "vision": "aspirational future-state concept art, premium, visionary, domain-relevant atmosphere",
    "call_to_action": "confident closing concept illustration, refined keynote mood, decisive and memorable",
}


def _gpu_memory_gb() -> float:
    if not torch.cuda.is_available():
        return 0.0
    try:
        props = torch.cuda.get_device_properties(0)
        return float(props.total_memory) / float(1024 ** 3)
    except Exception:
        return 0.0


def _default_cache_root() -> Path:
    custom = os.getenv("VENTUREOS_MODEL_CACHE_DIR", "").strip()
    if custom:
        return Path(custom).expanduser()
    d_drive = Path("D:/ventureos-model-cache")
    if d_drive.drive and Path("D:/").exists():
        return d_drive
    return Path(__file__).resolve().parent.parent / ".model-cache"


MODEL_CACHE_DIR = _default_cache_root()
GENERATED_DIR = Path(__file__).resolve().parent.parent / "static" / "generated" / "slide_images"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

_PIPELINE_LOCK = threading.Lock()
_PIPELINE_CACHE: Dict[str, object] = {}


def get_supported_models() -> List[dict]:
    models = []
    for key, meta in SUPPORTED_IMAGE_MODELS.items():
        models.append(
            {
                "key": key,
                "repo_id": meta["id"],
                "label": meta["label"],
            }
        )
    return models


def get_image_style_options() -> List[dict]:
    return [
        {"key": key, "label": meta["label"]}
        for key, meta in IMAGE_STYLE_PRESETS.items()
    ]


def get_image_coverage_options() -> List[dict]:
    return [
        {"key": key, "label": meta["label"]}
        for key, meta in IMAGE_COVERAGE_OPTIONS.items()
    ]


def _device_config() -> dict:
    forced = os.getenv("VENTUREOS_IMAGE_DEVICE", "").strip().lower()
    forced_dtype = os.getenv("VENTUREOS_IMAGE_DTYPE", "").strip().lower()
    if forced_dtype in {"float", "float32", "fp32"}:
        cuda_dtype = torch.float32
    elif forced_dtype in {"half", "float16", "fp16"}:
        cuda_dtype = torch.float16
    else:
        cuda_dtype = torch.float32 if _gpu_memory_gb() <= 6.0 else torch.float16
    if forced == "cpu":
        return {
            "device": "cpu",
            "dtype": torch.float32,
            "variant": None,
        }
    if forced == "cuda" and torch.cuda.is_available():
        return {
            "device": "cuda",
            "dtype": cuda_dtype,
            "variant": None,
        }
    if torch.cuda.is_available():
        return {
            "device": "cuda",
            "dtype": cuda_dtype,
            "variant": None,
        }
    return {
        "device": "cpu",
        "dtype": torch.float32,
        "variant": None,
    }


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-") or "slide"


def _digest(payload: dict) -> str:
    return hashlib.sha1(
        json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()[:12]


def _get_pipeline(model_key: str):
    config = SUPPORTED_IMAGE_MODELS.get(model_key) or SUPPORTED_IMAGE_MODELS["tiny-sd"]
    if model_key in _PIPELINE_CACHE:
        return _PIPELINE_CACHE[model_key]

    device_info = _device_config()
    kwargs = {
        "cache_dir": str(MODEL_CACHE_DIR),
        "torch_dtype": device_info["dtype"],
        "safety_checker": None,
        "requires_safety_checker": False,
        "low_cpu_mem_usage": True,
    }
    if device_info["variant"]:
        kwargs["variant"] = device_info["variant"]

    with _PIPELINE_LOCK:
        if model_key in _PIPELINE_CACHE:
            return _PIPELINE_CACHE[model_key]

        load_attempts = [
            {**kwargs, "use_safetensors": True},
            {**{k: v for k, v in kwargs.items() if k != "variant"}, "use_safetensors": True},
            {**{k: v for k, v in kwargs.items() if k != "variant"}, "use_safetensors": False},
            {**kwargs, "use_safetensors": False},
        ]
        last_error = None
        pipe = None
        loader = DiffusionPipeline.from_pretrained if config.get("loader") == "diffusion" else AutoPipelineForText2Image.from_pretrained
        for attempt in load_attempts:
            try:
                pipe = loader(config["id"], **attempt)
                break
            except Exception as exc:
                last_error = exc
        if pipe is None:
            raise last_error

        if hasattr(pipe, "scheduler") and pipe.scheduler is not None:
            try:
                if config.get("scheduler") == "deis":
                    pipe.scheduler = DEISMultistepScheduler.from_config(pipe.scheduler.config)
                elif config.get("scheduler") == "lcm":
                    pipe.scheduler = LCMScheduler.from_config(pipe.scheduler.config)
            except Exception:
                pass

        if hasattr(pipe, "set_progress_bar_config"):
            pipe.set_progress_bar_config(disable=True)
        if hasattr(pipe, "enable_attention_slicing"):
            pipe.enable_attention_slicing()

        if device_info["device"] == "cuda":
            if hasattr(pipe, "enable_model_cpu_offload"):
                pipe.enable_model_cpu_offload()
            else:
                pipe = pipe.to("cuda")
            if hasattr(pipe, "enable_vae_slicing"):
                pipe.enable_vae_slicing()
        else:
            pipe = pipe.to("cpu")

        _PIPELINE_CACHE[model_key] = pipe
        return pipe


def _pick_image_model() -> str:
    if DEFAULT_MODEL_KEY in SUPPORTED_IMAGE_MODELS:
        return DEFAULT_MODEL_KEY
    return "tiny-sd"


def _normalize_image_options(image_options: Optional[dict]) -> dict:
    image_options = image_options if isinstance(image_options, dict) else {}
    style = (image_options.get("style") or DEFAULT_IMAGE_STYLE).strip().lower()
    coverage = (image_options.get("coverage") or DEFAULT_IMAGE_COVERAGE).strip().lower()
    return {
        "enabled": bool(image_options.get("enabled", True)) and style != "none",
        "style": style if style in IMAGE_STYLE_PRESETS else "auto",
        "coverage": coverage if coverage in IMAGE_COVERAGE_OPTIONS else "key-slides",
        "variation_key": str(image_options.get("variation_key") or "").strip(),
    }


def predownload_models(model_keys: Optional[List[str]] = None) -> List[dict]:
    prepared = []
    keys = model_keys or [_pick_image_model()]
    for key in keys:
        config = SUPPORTED_IMAGE_MODELS.get(key)
        if not config:
            continue
        _get_pipeline(key)
        prepared.append(
            {
                "key": key,
                "repo_id": config["id"],
                "label": config["label"],
            }
        )
    return prepared


def _truncate_prompt_words(prompt: str, limit: int = 45) -> str:
    words = re.split(r"\s+", re.sub(r"\s+", " ", prompt).strip())
    if len(words) <= limit:
        return " ".join(words).strip()
    trimmed = " ".join(words[:limit]).rstrip(",.;: ")
    return f"{trimmed}."


def build_slide_image_prompt(
    idea: str,
    slide: dict,
    market_research: Optional[dict] = None,
    image_options: Optional[dict] = None,
) -> str:
    market_research = market_research or {}
    image_options = _normalize_image_options(image_options)
    target_customer = (market_research.get("target_customer") or "").strip()
    title = (slide.get("title") or "").strip()
    visual = (slide.get("visual_suggestion") or "").strip()
    subtitle = (slide.get("subtitle") or "").strip()
    slide_type = (slide.get("type") or "").strip().lower()
    layout = (slide.get("layout") or "").strip().lower()
    style_meta = IMAGE_STYLE_PRESETS.get(image_options["style"], IMAGE_STYLE_PRESETS["auto"])
    composition = SLIDE_IMAGE_DIRECTIVES.get(
        slide_type,
        "contextual editorial visual, clean focal hierarchy, strong negative space, non-photoreal",
    )
    subject_parts = []
    if idea:
        subject_parts.append(_truncate_prompt_words(idea, 8).rstrip("."))
    if title:
        subject_parts.append(title)
    detail_line = visual or subtitle
    if detail_line:
        subject_parts.append(_truncate_prompt_words(detail_line, 10).rstrip("."))
    if target_customer:
        subject_parts.append(f"for {_truncate_prompt_words(target_customer, 5).rstrip('.')}")

    composition_brief = _truncate_prompt_words(composition, 8).rstrip(".")
    tone_parts = [
        style_meta["label"].lower(),
        composition_brief,
        "dark editorial slide illustration",
        "no text",
        "non-photoreal",
    ]
    if layout in {"cover", "closing"}:
        tone_parts.append("hero framing")

    prompt = f"{', '.join([part for part in subject_parts if part])}. {', '.join(tone_parts)}."
    prompt = re.sub(r"\s+", " ", prompt).strip()
    return prompt


def _select_image_slide_indices(slides: List[dict], image_options: Optional[dict] = None) -> set:
    image_options = _normalize_image_options(image_options)
    if not image_options["enabled"] or not slides:
        return set()

    coverage = image_options["coverage"]
    anchors = [0]
    if len(slides) > 1:
        anchors.append(len(slides) - 1)
    if coverage == "all":
        return set(range(len(slides)))

    if coverage == "hero-only":
        return set(anchors)

    preferred_types = {
        "hook",
        "problem",
        "stakes",
        "solution",
        "impact",
        "vision",
        "call_to_action",
    }
    preferred = [
        index for index, slide in enumerate(slides)
        if index not in anchors and (slide.get("type") or "").lower() in preferred_types
    ]
    supplemental = [
        index for index, slide in enumerate(slides)
        if index not in anchors and index not in preferred
        and (slide.get("layout") or "").lower() not in {"comparison"}
    ]
    ordered = []
    for index in anchors + preferred + supplemental:
        if index not in ordered:
            ordered.append(index)

    configured_limit = IMAGE_COVERAGE_OPTIONS.get(coverage, {}).get("limit")
    if configured_limit is None:
        configured_limit = MAX_GENERATED_SLIDE_IMAGES
    limit = max(1, int(configured_limit))
    return set(ordered[:limit])


def generate_slide_image(
    *,
    idea: str,
    slide: dict,
    index: int,
    market_research: Optional[dict] = None,
    model_key: Optional[str] = None,
    image_options: Optional[dict] = None,
    force: bool = False,
) -> Optional[dict]:
    model_key = model_key or _pick_image_model()
    model_key = model_key if model_key in SUPPORTED_IMAGE_MODELS else "tiny-sd"
    config = SUPPORTED_IMAGE_MODELS[model_key]
    normalized_image_options = _normalize_image_options(image_options)
    prompt = build_slide_image_prompt(
        idea,
        slide,
        market_research=market_research,
        image_options=normalized_image_options,
    )

    key_payload = {
        "idea": idea,
        "slide": slide.get("title"),
        "visual": slide.get("visual_suggestion"),
        "subtitle": slide.get("subtitle"),
        "model": model_key,
        "image_style": normalized_image_options["style"],
        "variation_key": normalized_image_options["variation_key"],
    }
    digest = _digest(key_payload)
    file_name = f"{index + 1:02d}-{_slugify(slide.get('title') or f'slide-{index + 1}')}-{digest}.png"
    output_path = GENERATED_DIR / file_name
    if output_path.exists() and not force:
        return {
            "image_url": f"/static/generated/slide_images/{file_name}",
            "image_prompt": prompt,
            "image_model": config["label"],
            "image_repo_id": config["id"],
            "image_status": "cached",
        }

    pipe = _get_pipeline(model_key)
    device = _device_config()["device"]
    generator = torch.Generator(device=device).manual_seed(1000 + index)
    inference_kwargs = {
        "prompt": prompt,
        "negative_prompt": DEFAULT_NEGATIVE_PROMPT,
        "num_inference_steps": int(config["steps"]),
        "guidance_scale": float(config["guidance_scale"]),
        "width": int(config["width"]),
        "height": int(config["height"]),
        "generator": generator,
    }
    if config.get("scheduler") == "lcm":
        inference_kwargs["lcm_origin_steps"] = int(config.get("lcm_origin_steps", 50))

    result = pipe(
        **inference_kwargs,
    )
    image = result.images[0]
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = image.resize((768, 768), Image.LANCZOS)
    image.save(output_path, format="PNG", optimize=True)

    return {
        "image_url": f"/static/generated/slide_images/{file_name}",
        "image_prompt": prompt,
        "image_model": config["label"],
        "image_repo_id": config["id"],
        "image_status": "generated",
    }


def enrich_slides_with_images(
    *,
    idea: str,
    slides: List[dict],
    market_research: Optional[dict] = None,
    model_key: Optional[str] = None,
    image_options: Optional[dict] = None,
) -> List[dict]:
    normalized_image_options = _normalize_image_options(image_options)
    selected_indices = _select_image_slide_indices(slides, normalized_image_options)
    enriched = []
    for index, slide in enumerate(slides):
        enriched_slide = dict(slide)
        if index in selected_indices:
            try:
                image_meta = generate_slide_image(
                    idea=idea,
                    slide=enriched_slide,
                    index=index,
                    market_research=market_research,
                    model_key=model_key,
                    image_options=normalized_image_options,
                )
                if image_meta:
                    enriched_slide.update(image_meta)
            except Exception as exc:
                enriched_slide["image_error"] = str(exc)
                enriched_slide["image_status"] = "failed"
        enriched.append(enriched_slide)
    return enriched
