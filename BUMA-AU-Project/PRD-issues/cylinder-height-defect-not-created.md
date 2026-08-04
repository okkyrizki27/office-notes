# Task Cylinder Height — Defect Not Created When Result Out of Spec

| | |
|---|---|
| **Project** | BUMA AU |
| **Reported by** | Benedict Panizza |
| **Date Raised** | TBD |
| **Status** | Investigated |

## Description

Task Cylinder Height does not create a defect when the result is out of spec.

## Investigation Result

This task only creates a defect when both conditions are met:

1. Supervisor Adjustment = Yes, **and**
2. The result of the adjustment is still out of spec.

If Supervisor Adjustment = No, no defect is created even though the original result is out of spec.
