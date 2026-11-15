# Sample with Git diff3 conflict markers (including Common Ancestor)

def process_transaction(amount, account_id):
<<<<<<< HEAD
    # Branch: performance-cache
    print(f"DEBUG: Checking fast cache for account {account_id}")
    return execute_cached_payment(amount, account_id)
||||||| 7a8b9c0 (Common Ancestor)
    # Original Base Implementation
    return execute_standard_payment(amount, account_id)
=======
    # Branch: security-audit
    log_security_audit(account_id, amount)
    return execute_verified_payment(amount, account_id)
>>>>>>> security-audit

# End of module
