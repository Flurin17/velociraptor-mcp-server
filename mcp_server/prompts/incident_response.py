INCIDENT_RESPONSE_PROMPTS = {
    "investigate_process": (
        "You are triaging a suspicious process on an endpoint. "
        "Gather process details, network connections, binaries on disk, "
        "and recent alerts for the client."
    ),
    "analyze_network": (
        "Enumerate active network connections, listening ports, and recent DNS lookups. "
        "Highlight anomalies or connections to risky destinations."
    ),
    "collect_forensics": (
        "Collect core forensic artifacts (autoruns, processes, users, services) "
        "from a target client or hunt cohort."
    ),
}
