.
├── db.py            # Database initialization and low-level access
├── services/        # Business logic and DAO layer
│   ├── __init__.py
│   ├── users.py
│   ├── chats.py
│   ├── inventory.py
│   ├── orders.py
│   └── settings.py
├── handlers/        # Telegram handlers
│   ├── __init__.py
│   ├── start.py
│   ├── order_flow.py
│   ├── operator.py
│   └── admin.py
├── keyboards.py     # Keyboards builders
├── states.py        # FSM states definitions
├── config.py        # Configuration loader
├── main.py          # Bot entry point
├── seed.py          # Demo data seeding script
├── tests/           # Unit tests
│   ├── test_inventory.py
│   └── test_chats.py
└── README.md        # Usage instructions
