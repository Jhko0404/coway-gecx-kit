def set_session_state(_action_trigger: str = "",
                      _escalation_reason: str = "",
                      _escalation_topic: str = "") -> dict:
    """Write trigger and escalation variables to session state.

    Args:
        _action_trigger: Action to trigger (e.g., 'escalate'). Read by before_model_callback.
        _escalation_reason: Brief reason for escalation. Read by before_model_callback.
        _escalation_topic: Main topic (e.g., 'billing', 'general'). Read by before_model_callback.

    Returns:
        dict: Confirmation of which variables were set.
    """
    updated = {}
    if _action_trigger:
        context.state["_action_trigger"] = _action_trigger
        updated["_action_trigger"] = _action_trigger
    if _escalation_reason:
        context.state["_escalation_reason"] = _escalation_reason
        updated["_escalation_reason"] = _escalation_reason
    if _escalation_topic:
        context.state["_escalation_topic"] = _escalation_topic
        updated["_escalation_topic"] = _escalation_topic

    if not updated:
        return {
            "agent_action": "At least one parameter must be provided to set_session_state."
        }

    return {
        "status": "success",
        "updated_variables": updated,
    }
