# Examples

## basic_usage.py

Uses DRAFT Protocol as a Python library — no server needed.

Demonstrates the full lifecycle:
1. Classify a message into a governance tier
2. Create a session
3. Map all 5 DRAFT dimensions against context
4. Generate elicitation questions for gaps
5. Confirm fields with human answers
6. Surface assumptions
7. Check the confirmation gate

```bash
python examples/basic_usage.py
```

No dependencies beyond `draft-protocol` itself. Uses a temporary SQLite database.
