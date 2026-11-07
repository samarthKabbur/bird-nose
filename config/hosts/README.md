# Host roles

Versioned, non-secret settings for each kind of computer. Machine-local
values (addresses, passwords) never go here; they belong in that machine's
untracked `containers/.env`.

| File | Computer | ROS domain | Discovery |
| --- | --- | --- | --- |
| `workstation.env` | Ubuntu laptop (development, simulation, operator) | 42 | LOCALHOST |
| `nuvo.env` | Nuvo, primary onboard computer | 0 | SUBNET |
| `bender.env` | bender, secondary onboard computer | 0 | SUBNET |

Which sensor drivers run on Nuvo and which on bender is decided in Phase 5.
