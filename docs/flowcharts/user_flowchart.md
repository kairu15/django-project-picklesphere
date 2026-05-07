# User Flowchart - PickleSphere

```mermaid
flowchart TD
    A((Start)) --> B[Login/Register]
    B --> C{Authenticated?}
    C -->|No| B
    C -->|Yes| D[User Dashboard]

    D --> E{Choose Action}

    E -->|Reservations| F[Browse Courts]
    F --> G[Select Court & Time]
    G --> H[Make Reservation]
    H --> I[Payment]
    I --> D

    E -->|My Reservations| J[View/Cancel Reservations]
    J --> D

    E -->|Tournaments| K[Browse Tournaments]
    K --> L[Register & Pay]
    L --> M[Play Matches]
    M --> D

    E -->|Equipment| N[Browse Equipment]
    N --> O[Rent Equipment]
    O --> P[Link to Reservation]
    P --> I

    E -->|Profile| Q[View/Edit Profile]
    Q --> D

    E -->|Logout| R((End))
```

## User Actions Summary

| Module | Actions |
|--------|---------|
| **Auth** | Register → Login → Dashboard |
| **Reservations** | Browse → Book → Pay → Play |
| **Tournaments** | Browse → Register → Compete |
| **Equipment** | Browse → Rent → Pay |
| **Profile** | View/Edit personal info |
