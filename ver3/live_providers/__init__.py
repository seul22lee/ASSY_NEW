"""Live model providers — implementations that actually contact a network.

WHY THIS PACKAGE IS NOT INSIDE assy_v3
    ver3/tests/meta/test_no_stage_implementation.py forbids importing urllib,
    http, socket, requests, httpx, openai or anthropic anywhere under
    ver3/assy_v3, on the principle that "a boundary that can already make a call
    is not a boundary". The pipeline package declares the provider INTERFACE and
    nothing that can reach a server.

    A live provider therefore lives here, outside the protected tree, and is
    injected into a stage exactly like the offline one. The dependency runs one
    way only: this package imports the interface from assy_v3, and assy_v3 never
    imports this.

WHAT LIVES HERE
    deepseek.py   DeepSeek chat-completions, an independent live provider
    env.py        loads a git-ignored .env into the process environment

No module here is imported by the pipeline, by a stage, or by a contract test.
"""
