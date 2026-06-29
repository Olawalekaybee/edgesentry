"""Events layer — turns vision detections into durable, queryable facts.

    models.py    the Event schema (one row = one thing that happened)
    store.py     SQLite persistence + structured queries (exact counts, filters)
    ingestor.py  bridges perception → Event → both the SQLite store and the
                 RAG vector store, with debouncing so a lingering person does
                 not create thousands of duplicate events.

Two stores on purpose: SQLite answers *precise* questions ("how many events in
Zone 2 after 14:00?"), the vector store answers *fuzzy* ones ("anything that
looked unusual?"). The agent uses whichever fits the question.
"""
