def listing_fields(presentation):
    return {
        "listing_view": [field["label"] for field in presentation],
        "field_mapping": {field["label"]: field["value"] for field in presentation},
    }
