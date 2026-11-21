# Main LifeTimeLine entryoint app

## Entity cards

Exercise, program, workout, workout history, and member listings use the shared
[`entity_card_view.html`](../../common/templates/entity_card_view.html) template.
Each entity's `card_presentation` defines functions for the title, image, and
ordered body fields, plus applicable action IDs. The listing routes provide
action URLs, methods, targets, labels, icons, and whether each action is enabled
in that context. The footer displays each available action's label and optional
icon. An optional `button_label` provides shorter visible text while `label`
remains the accessible name and tooltip. Missing or empty body values and
unavailable actions are hidden.

Each entity's `list_presentation` specifies ordered labels and value functions;
the listing routes use this metadata for table columns. Exercise facets remain in
[`active_fitness_registry.py`](../../common/fitness/active_fitness_registry.py).
To add a card or list field, add a label and value function to the corresponding
entity presentation metadata; keep action IDs and route configuration in sync.
