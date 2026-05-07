function label_severity(tag, timestamp, record)
    local msg = record["log"] or record["message"] or ""
    local lower = string.lower(msg)

    record["severity"] = "low"
    record["category"] = "application"

    if string.find(lower, "dlp_hit") or string.find(lower, "policy_violation") or string.find(lower, "ferpa") or string.find(lower, "hipaa") then
        record["severity"] = "high"
        record["category"] = "policy_violation"
    elseif string.find(lower, "auth_failure") or string.find(lower, "failed login") or string.find(lower, "unauthorized") or string.find(lower, "forbidden") then
        record["severity"] = "high"
        record["category"] = "authentication"
    elseif string.find(lower, "error") or string.find(lower, "exception") or string.find(lower, "traceback") then
        record["severity"] = "high"
        record["category"] = "runtime_error"
    elseif string.find(lower, "warn") or string.find(lower, "rate limit") then
        record["severity"] = "medium"
        record["category"] = "operational_warning"
    end

    return 1, timestamp, record
end
