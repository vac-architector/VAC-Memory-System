OFFICIAL_CATEGORY_LABELS = {1: 'Single-hop (Factual)', 2: 'Temporal', 3: 'Multi-hop', 4: 'Commonsense', 5: 'Adversarial'}

def label_for(category_id: int) -> str:
    try:
        key = int(category_id)
    except Exception:
        return f'Unknown({category_id})'
    return OFFICIAL_CATEGORY_LABELS.get(key, f'Unknown({category_id})')