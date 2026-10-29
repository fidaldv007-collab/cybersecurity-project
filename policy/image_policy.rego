package cybersecurity.policy

default allow = false

# Deny if any vulnerability is flagged as CRITICAL
deny[msg] {
    input.vulnerabilities[_].Severity == "CRITICAL"
    msg := "Deployment blocked: Critical vulnerability detected in image scan."
}

# Allow if no critical issues are found
allow {
    not deny[_]
}
