def lookup_customer(customer_id: str) -> dict:
    """Look up customer rental account details by customer ID.

    Args:
        customer_id: The customer's account ID.

    Returns:
        dict: Account details or error information.
    """
    auth_status = context.state.get("auth_status", "")
    if auth_status != "authenticated":
        return {
            "status": "error",
            "error": "Account lookup requires an authenticated session.",
            "agent_action": ("Inform the customer that you cannot access account "
                             "details without verification."),
        }

    if not customer_id:
        return {
            "status": "error",
            "error": "customer_id is required.",
            "agent_action": "Ask the customer for their customer ID.",
        }

    try:
        account_data = {
            "status": "success",
            "account": {
                "customer_id": customer_id,
                "plan": "Purifier Care Membership",
                "balance": "0원",
                "next_billing_date": "2099-01-15",
                "service_status": "active",
            },
        }
        return account_data

    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to retrieve account: {str(e)}",
            "agent_action": ("Inform the customer that you are unable to access "
                             "their account details at this time and offer to "
                             "connect them with a specialist."),
        }
