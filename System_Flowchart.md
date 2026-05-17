# PickleSphere System Flowchart

This flowchart shows the main process of the PickleSphere system using standard flowchart symbols.

## Legend

- **Start/End**: Terminal shape, not a circle
- **Input/Output**: Parallelogram
- **Process**: Rectangle
- **Decision**: Diamond
- **On-page connector**: Small circle used to continue the flow on the same page

## System Flowchart

```mermaid
flowchart TD
    Start([Start])
    Open[/User opens PickleSphere system/]
    LoginChoice{Does the user have an account?}
    Register[Register user account]
    Login[/Enter login credentials/]
    Validate{Are credentials valid?}
    Retry[/Show login error and request credentials again/]
    Dashboard[Display user dashboard]
    RoleCheck{Is the user an administrator?}

    AdminMenu[/Select admin function/]
    ManageCourts[Manage courts and schedules]
    ManageEquipment[Manage equipment inventory]
    ManageTournaments[Manage tournaments]
    ViewReports[/View system reports/]

    UserMenu[/Select user function/]
    CheckCourt[/Check court availability/]
    Reserve[Create court reservation]
    RentEquipment[Request equipment rental]
    JoinTournament[Register for tournament]
    RecordScore[/Enter game score/]

    ConnectorA((A))
    PaymentNeeded{Is payment required?}
    Payment[/Submit payment details/]
    Confirm[Save transaction and booking details]
    Notify[/Send confirmation notification/]
    End([End])

    Start --> Open
    Open --> LoginChoice
    LoginChoice -- No --> Register
    Register --> Login
    LoginChoice -- Yes --> Login
    Login --> Validate
    Validate -- No --> Retry
    Retry --> Login
    Validate -- Yes --> Dashboard
    Dashboard --> RoleCheck

    RoleCheck -- Yes --> AdminMenu
    AdminMenu --> ManageCourts
    AdminMenu --> ManageEquipment
    AdminMenu --> ManageTournaments
    AdminMenu --> ViewReports
    ManageCourts --> ConnectorA
    ManageEquipment --> ConnectorA
    ManageTournaments --> ConnectorA
    ViewReports --> ConnectorA

    RoleCheck -- No --> UserMenu
    UserMenu --> CheckCourt
    CheckCourt --> Reserve
    UserMenu --> RentEquipment
    UserMenu --> JoinTournament
    UserMenu --> RecordScore
    Reserve --> ConnectorA
    RentEquipment --> ConnectorA
    JoinTournament --> ConnectorA
    RecordScore --> ConnectorA

    ConnectorA --> PaymentNeeded
    PaymentNeeded -- Yes --> Payment
    Payment --> Confirm
    PaymentNeeded -- No --> Confirm
    Confirm --> Notify
    Notify --> End
```

