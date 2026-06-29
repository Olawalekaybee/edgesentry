"""Web layer — the dashboard, live event stream, and chat endpoint.

    app.py     Flask app factory; registers routes and holds shared objects
    routes.py  HTTP routes: index page, /api/chat (agent), /api/events (history)
    sse.py     Server-Sent Events stream for the live feed (reused from v1)

The big v2 addition here is /api/chat: it hands the user's message to the Agent
and returns the answer, powering the chat box next to the live camera feed.
"""
