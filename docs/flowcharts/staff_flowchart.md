# Staff Flowchart - PickleSphere

```mermaid
flowchart TD
    A((Start)) --> B[Staff Login]
    B --> C{Staff Role?}
    C -->|No| D[Access Denied]
    C -->|Yes| E[Staff Dashboard]

    E --> F{Choose Action}

    F -->|Reservations| G[View All Reservations]
    G --> H{Action}
    H -->|Approve| I[Approve & Notify]
    H -->|Reject| J[Reject with Reason]
    I --> E
    J --> E

    F -->|Payments| K[View Payments]
    K --> L{Verify}
    L -->|GCash| M[Verify Proof Image]
    L -->|Cash| N[Record & Receipt]
    M --> E
    N --> E

    F -->|Equipment| O[View Inventory]
    O --> P{Process}
    P -->|Checkout| Q[Reserved → Rented]
    P -->|Checkin| R[Inspect & Complete]
    Q --> E
    R --> E

    F -->|Calendar| S[View Calendar]
    S --> E

    F -->|Logout| T((End))
```

## Staff Permissions

| Module | Permissions |
|--------|-------------|
| **Reservations** | View all, Approve/Reject |
| **Payments** | Verify GCash/Cash payments |
| **Equipment** | Checkout/Checkin only |
| **Users** | View only |
| **Tournaments** | Approve registrations |
| **Content** | No access |
