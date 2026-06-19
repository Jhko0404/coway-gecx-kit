def update_language(new_language: str = "") -> dict:
    """Set the active conversation language when the customer explicitly asks to switch.

    Call this BEFORE producing your first response in the new language.

    Args:
        new_language: 'English' or 'Korean' (REQUIRED).

    Returns:
        dict with the active_language and an agent_action.
    """
    valid = {"english": "English", "korean": "Korean"}
    key = (new_language or "").strip().lower()
    if key not in valid:
        return {"status": "error", "error": "unsupported language",
                "agent_action": ("Ask whether they'd like English or Korean; stay "
                                 "in the current language for now.")}
    lang = valid[key]
    context.state["active_language"] = lang
    return {"status": "success", "active_language": lang,
            "agent_action": "Continue the entire conversation in " + lang + "."}
