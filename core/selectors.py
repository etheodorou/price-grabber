import yaml
from pathlib import Path

def load_selectors(site, category):
    config_path = Path(__file__).parent.parent / 'config' / 'selectors.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    try:
        return data[site][category]
    except KeyError:
        raise ValueError(f"Selectors for {site} - {category} not found in selectors.yaml")
