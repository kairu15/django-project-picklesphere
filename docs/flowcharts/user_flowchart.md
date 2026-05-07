# User Flowchart - PickleSphere

**Legend:**
- `(( ))` - Start/End (Terminal)
- `[/ /]` - Input/Output (Data)
- `{ }` - Process/Action (Rectangle)
- `{{ }}` - Decision (Diamond)
- `[/\\ /\\]` - Database/Storage

```mermaid
flowchart TD
    %% Styling
    classDef terminal fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef process fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    classDef decision fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    classDef data fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    classDef db fill:#fff8e1,stroke:#ff8f00,stroke-width:2px

    %% Start
    START((START)):::terminal

    %% Authentication Flow
    START --> AUTH{Already<br/>Logged In?}:::decision
    AUTH -->|No| REGISTER_LOGIN{New User?}:::decision
    REGISTER_LOGIN -->|Yes| REGISTER[/Register Account/]:::data
    REGISTER_LOGIN -->|No| LOGIN[/Login/]:::data
    AUTH -->|Yes| DASHBOARD{User Dashboard}:::process

    %% Registration & Login Process
    REGISTER --> VERIFY_EMAIL{Verify Email}:::decision
    VERIFY_EMAIL -->|Success| LOGIN
    LOGIN --> CHECK_ROLE{Check User Role}:::decision
    CHECK_ROLE -->|User| DASHBOARD

    %% Main Dashboard Navigation
    DASHBOARD --> NAV{Choose Action}:::decision

    %% === RESERVATIONS BRANCH ===
    NAV -->|Reservations| RES_MENU{Reservation Action}:::decision

    RES_MENU -->|View Courts| VIEW_COURTS[/Browse Courts/]:::data
    VIEW_COURTS --> FILTER_COURTS{Filter by<br/>Location/Type}:::decision
    FILTER_COURTS --> SELECT_COURT{Select Court}:::decision
    SELECT_COURT --> CHECK_AVAIL{Check Availability}:::decision
    CHECK_AVAIL -->|Available| MAKE_RES[/Make Reservation/]:::data
    CHECK_AVAIL -->|Unavailable| VIEW_COURTS
    MAKE_RES --> PAYMENT_FLOW

    RES_MENU -->|My Reservations| MY_RES[/View My Reservations/]:::data
    MY_RES --> RES_ACTION{Action}:::decision
    RES_ACTION -->|View Details| VIEW_RES_DETAIL[/Reservation Details/]:::data
    RES_ACTION -->|Cancel| CANCEL_RES{Cancel Reservation}:::process
    CANCEL_RES --> REFUND{Refund?}:::decision
    REFUND -->|Yes| PROCESS_REFUND[/Process Refund/]:::data
    REFUND -->|No| MY_RES
    RES_MENU -->|Calendar| VIEW_CAL[/View Calendar/]:::data

    %% === PAYMENT BRANCH ===
    PAYMENT_FLOW --> SELECT_PAY{Payment Method}:::decision
    SELECT_PAY -->|Credit Card| CARD_PAY[/Enter Card Details/]:::data
    SELECT_PAY -->|GCash| GCASH_PAY[/Upload GCash Proof/]:::data
    SELECT_PAY -->|Cash| CASH_PAY[/Pay at Counter/]:::data

    CARD_PAY --> PROCESS_PAY{Process Payment}:::decision
    GCASH_PAY --> PENDING_VER{Pending<br/>Verification}:::decision
    CASH_PAY --> PENDING_VER

    PROCESS_PAY -->|Success| PAY_SUCCESS[/Payment Confirmed/]:::data
    PROCESS_PAY -->|Failed| RETRY_PAY{Retry?}:::decision
    RETRY_PAY -->|Yes| SELECT_PAY
    RETRY_PAY -->|No| CANCEL_PAY[/Cancel/]:::data

    PENDING_VER -->|Approved| PAY_SUCCESS
    PENDING_VER -->|Rejected| RETRY_PAY

    PAY_SUCCESS --> RECEIPT[/View/Print Receipt/]:::data
    RECEIPT --> DASHBOARD

    %% === TOURNAMENTS BRANCH ===
    NAV -->|Tournaments| TOUR_MENU{Tournament Action}:::decision
    TOUR_MENU -->|Browse| VIEW_TOUR[/View Tournaments/]:::data
    VIEW_TOUR --> TOUR_DETAIL[/Tournament Details/]:::data
    TOUR_DETAIL --> REGISTER_TOUR{Register?}:::decision
    REGISTER_TOUR -->|Yes| PAY_FEE[/Pay Entry Fee/]:::data
    PAY_FEE --> REG_CONFIRM[/Registration Confirmed/]:::data
    REGISTER_TOUR -->|No| VIEW_TOUR

    TOUR_MENU -->|My Tournaments| MY_TOUR[/My Tournament Registrations/]:::data
    TOUR_MENU -->|My Matches| MY_MATCHES[/View My Matches/]:::data
    MY_MATCHES --> MATCH_DETAIL[/Match Details/]:::data
    MATCH_DETAIL --> SUBMIT_SCORE{Submit Score}:::decision
    SUBMIT_SCORE -->|Yes| SCORE_FORM[/Enter Score/]:::data
    SUBMIT_SCORE -->|No| MY_MATCHES

    %% === EQUIPMENT BRANCH ===
    NAV -->|Equipment| EQUIP_MENU{Equipment Action}:::decision
    EQUIP_MENU -->|Browse| VIEW_EQUIP[/View Equipment/]:::data
    VIEW_EQUIP --> SELECT_EQUIP{Select Equipment}:::decision
    SELECT_EQUIP --> CHECK_STOCK{Check Stock}:::decision
    CHECK_STOCK -->|Available| RENT_EQUIP[/Rent Equipment/]:::data
    CHECK_STOCK -->|Unavailable| VIEW_EQUIP
    RENT_EQUIP --> ADD_RES{Add to<br/>Reservation?}:::decision
    ADD_RES -->|Yes| LINK_RES[/Link to Reservation/]:::data
    ADD_RES -->|No| RENT_EQUIP
    LINK_RES --> PAYMENT_FLOW

    EQUIP_MENU -->|My Rentals| MY_RENTALS[/View My Rentals/]:::data
    MY_RENTALS --> RENTAL_ACTION{Action}:::decision
    RENTAL_ACTION -->|Cancel| CANCEL_RENTAL{Cancel Rental}:::process

    %% === PROFILE BRANCH ===
    NAV -->|Profile| PROFILE_MENU{Profile Action}:::decision
    PROFILE_MENU -->|View| VIEW_PROFILE[/View Profile/]:::data
    PROFILE_MENU -->|Edit| EDIT_PROFILE[/Edit Profile/]:::data
    EDIT_PROFILE --> SAVE_PROFILE{Save Changes}:::decision
    SAVE_PROFILE -->|Success| DASHBOARD
    SAVE_PROFILE -->|Error| EDIT_PROFILE
    PROFILE_MENU -->|Stats| VIEW_STATS[/View Player Stats/]:::data

    %% === RATINGS BRANCH ===
    NAV -->|Ratings| RATE_MENU{Rating Action}:::decision
    RATE_MENU -->|Pending| PENDING_RATES[/Pending Ratings/]:::data
    PENDING_RATES --> SUBMIT_RATE[/Submit Rating/]:::data
    RATE_MENU -->|My Reviews| MY_RATINGS[/My Ratings/]:::data

    %% === NOTIFICATIONS ===
    NAV -->|Notifications| VIEW_NOTIF[/View Notifications/]:::data
    VIEW_NOTIF --> NOTIF_ACTION{Action}:::decision
    NOTIF_ACTION -->|Mark Read| MARK_READ{Mark as Read}:::process
    NOTIF_ACTION -->|Dismiss| DISMISS_NOTIF{Dismiss}:::process

    %% === SUPPORT ===
    NAV -->|Support| CONTACT[/Contact Support/]:::data
    CONTACT --> SEND_MSG[/Send Message/]:::data
    SEND_MSG --> MSG_CONFIRM[/Message Sent/]:::data

    %% Logout
    NAV -->|Logout| LOGOUT{Logout}:::process
    LOGOUT --> END((END)):::terminal

    %% Return paths
    MARK_READ --> DASHBOARD
    DISMISS_NOTIF --> DASHBOARD
    MSG_CONFIRM --> DASHBOARD
    CANCEL_RENTAL --> DASHBOARD
    REG_CONFIRM --> DASHBOARD
    SCORE_FORM --> DASHBOARD
    SUBMIT_RATE --> DASHBOARD
    VIEW_STATS --> DASHBOARD
    VIEW_RES_DETAIL --> DASHBOARD
    PROCESS_REFUND --> DASHBOARD
    CANCEL_PAY --> DASHBOARD
    VIEW_NOTIF --> DASHBOARD
```

## Flow Summary

| Section | Key Actions | Data Flow |
|---------|-------------|-----------|
| **Authentication** | Register → Login → Role Check | User DB ← Credentials |
| **Reservations** | Browse → Filter → Select → Book → Pay | Court DB ← Availability |
| **Payments** | Select Method → Process → Confirmation | Payment Gateway |
| **Tournaments** | Browse → Register → Pay → Compete | Tournament DB |
| **Equipment** | Browse → Check Stock → Rent → Link → Pay | Equipment DB |
| **Profile** | View/Edit → Save | User Profile DB |
| **Ratings** | Pending → Submit Review | Ratings DB |
