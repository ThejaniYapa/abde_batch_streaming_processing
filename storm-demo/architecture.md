             ┌──────────┐
             │ Storm UI │  → http://localhost:8080
             └────┬─────┘
                  │
            ┌─────▼─────┐
            │  Nimbus   │  (Topology scheduler)
            └─────┬─────┘
                  │
        ┌─────────▼─────────┐
        │    Zookeeper      │  (Coordination)
        └─────────┬─────────┘
                  │
     ┌────────────▼────────────┐
     │      Supervisors         │
     │  (Workers / Executors)   │
     └─────────────────────────┘
