# Codex Mapping

| Core requirement | Mapping | Notes |
| --- | --- | --- |
| Leader/dispatcher role separation | native | Separate tasks and completion packets. |
| Role delegation | native | Delegate bounded work packages only. |
| Artifact/schema validation | tool | Run included validator and project checks. |
| Gate decision record | prompt | Leader writes the canonical record. |
| Pre-production deployment | manual | Human supplies approval; authorised tool executes it. |
| Deployment evidence capture | tool | Bind logs and smoke evidence to the candidate version. |
