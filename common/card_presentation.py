def build_card_view(entity, presentation):
    rows = []
    for field in presentation["fields"]:
        value = field["value"](entity)
        if value is None or (isinstance(value, str) and not value.strip()):
            continue
        if isinstance(value, (list, tuple, dict, set)) and not value:
            continue
        rows.append({"label": field["label"], "value": value})

    return {
        "title": presentation["title"](entity),
        "image_url": presentation["image"](entity),
        "fields": rows,
        "actions": presentation["actions"],
    }


def build_card_views(entities, presentation):
    return [
        {**item, "card_view": build_card_view(item["entity"], presentation)}
        for item in entities
    ]
