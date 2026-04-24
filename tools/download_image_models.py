import json

from image_generation import get_supported_models, predownload_models


def main():
    models = get_supported_models()
    default_keys = [model["key"] for model in models if model["key"] in {"lcm-dreamshaper-v7", "tiny-sd"}]
    prepared = predownload_models(default_keys)
    print(json.dumps({"prepared": prepared}, indent=2))


if __name__ == "__main__":
    main()
