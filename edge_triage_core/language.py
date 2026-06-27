"""Language/radio-script formatting helpers for Edge-Triage."""

from __future__ import annotations

SUPPORTED_LANGUAGES = {"en", "es"}
SUPPORTED_FORMATS = {"standard", "radio"}

ES_LABELS = {
    "affected_injured_or_dead_people": "personas afectadas, heridas o fallecidas",
    "infrastructure_and_utility_damage": "daño a infraestructura o servicios",
    "rescue_volunteering_or_donation_effort": "rescate, voluntariado o donaciones",
    "not_humanitarian": "sin acción humanitaria clara",
}

ES_ACTION_PREFIX = {
    "affected_injured_or_dead_people": "Escalar a equipos médicos o de rescate capacitados.",
    "infrastructure_and_utility_damage": "Mantener a civiles alejados y avisar a infraestructura o servicios.",
    "rescue_volunteering_or_donation_effort": "Coordinar con logística antes de enviar voluntarios o suministros.",
    "not_humanitarian": "Mantener en revisión de baja prioridad salvo que aparezca contexto de desastre.",
}


def normalize_language(language: str | None) -> str:
    value = (language or "en").strip().lower()
    return value if value in SUPPORTED_LANGUAGES else "en"


def normalize_output_format(output_format: str | None) -> str:
    value = (output_format or "standard").strip().lower()
    return value if value in SUPPORTED_FORMATS else "standard"


def build_radio_script(label: str, action_pack: dict, language: str = "en") -> str:
    language = normalize_language(language)
    if language == "es":
        label_text = ES_LABELS.get(label, label.replace("_", " "))
        prefix = ES_ACTION_PREFIX.get(label, action_pack["safe_next_action"])
        return (
            f"Reporte de campo: posible {label_text}. {prefix} "
            f"Recoja ubicación, personas afectadas y peligros visibles. Apoyo a la decisión solamente; revisión humana requerida."
        )
    return (
        f"Field report: possible {label.replace('_', ' ')}. {action_pack['safe_next_action']} "
        f"Collect location, affected people, visible hazards, and access conditions. Decision support only; human review required."
    )
