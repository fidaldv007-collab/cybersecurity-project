package cybersecurity.policy

import rego.v1

default allow := false

# Block deployment if a critical vulnerability exists
deny contains "Critical vulnerability detected" if {
    some vuln in input.vulnerabilities
    vuln.Severity == "CRITICAL"
}

# Block deployment if image signature is not verified
deny contains "Image signature verification failed" if {
    input.signature_verified != true
}

# Block deployment if the container is privileged
deny contains "Privileged container deployment is prohibited" if {
    input.privileged == true
}

# Allow deployment only when no security rule is violated
allow if {
    count(deny) == 0
}
