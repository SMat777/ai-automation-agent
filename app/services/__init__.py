"""Service layer — business logic that sits between routers and agent tools.

Services orchestrate multiple tool calls, derive validation results, and shape
responses. Keeping them out of the routers keeps HTTP concerns separate from
domain logic.
"""
