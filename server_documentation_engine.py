"""
Protodex Server Documentation Engine
Provides rich, SEO-optimized technical overviews, agent capabilities,
and copyable AI agent prompts for Model Context Protocol servers.
"""

from html import escape
import re

# Comprehensive curated technical documentation for top/high-traffic MCP servers
CURATED_SERVER_DOCS = {
    "n8n-io/n8n": {
        "summary": "n8n is a leading fair-code workflow automation platform with extensive native AI capabilities. When integrated as an MCP server, it allows AI agents like Claude Desktop, Cursor, and Claude Code to discover, trigger, configure, and monitor multi-step automated workflows across 400+ SaaS apps, databases, and APIs without manual context switching.",
        "capabilities": [
            "Trigger complex multi-system workflows (Stripe, GitHub, Slack, Hubspot, Postgres) directly from LLM conversational turns.",
            "Inspect execution logs, debug failed workflow nodes, and verify payload data via natural language.",
            "Combine visual low-code pipelines with autonomous AI agent tool calls in self-hosted or cloud environments.",
            "Enforce granular authentication and data privacy by hosting n8n on your own local or private cloud infrastructure."
        ],
        "prompts": [
            "Trigger the 'New User Onboarding' workflow in n8n and report the execution status.",
            "List all active workflows in my n8n instance and verify when each one last ran.",
            "Create a new webhook trigger node in n8n to listen for incoming GitHub pull request events."
        ]
    },
    "modelcontextprotocol/servers": {
        "summary": "The official reference Model Context Protocol servers repository maintained by Anthropic and the open-source community. Provides production-tested reference implementations for filesystem access, PostgreSQL, SQLite, Slack, GitHub, Git, Google Drive, Brave Search, Memory graphs, and Puppeteer.",
        "capabilities": [
            "Connect AI assistants to local file systems, directories, and Git repositories with strict read/write sandboxing.",
            "Execute read-only SQL queries and schema introspection against PostgreSQL, MySQL, and SQLite databases.",
            "Bridge Claude and Cursor to team communication tools (Slack) and cloud storage (Google Drive).",
            "Provide long-term contextual graph memory across independent chat conversations."
        ],
        "prompts": [
            "Inspect the schema of my connected SQLite database and calculate weekly active signups.",
            "Search my project directory for all files that import the authentication middleware.",
            "Fetch recent unread messages from the #engineering Slack channel and summarize high-priority alerts."
        ]
    },
    "google-gemini/gemini-cli": {
        "summary": "Official CLI and Model Context Protocol bridge for Google Gemini models. Enables developers to route agent reasoning tasks, massive context analysis (up to 2M tokens), multimodal vision, and structured data generation directly into Google's latest Gemini 1.5 Pro and Flash models.",
        "capabilities": [
            "Access Gemini 1.5 Pro and Flash with massive 2M-token context windows directly from MCP client workflows.",
            "Process complex multimodal inputs including high-resolution images, audio, video files, and large PDF documents.",
            "Execute structured JSON extraction, benchmark evaluations, and multi-model consensus checks.",
            "Leverage Google Cloud developer knowledge and Google Search grounding within agent turns."
        ],
        "prompts": [
            "Send this 50-page PDF report to Gemini 1.5 Pro and extract an executive summary of financial risks.",
            "Analyze the attached architectural diagram image and describe any single points of failure.",
            "Compare the code refactoring suggestion between Claude and Gemini 1.5 Flash."
        ]
    },
    "microsoft/playwright-mcp": {
        "summary": "Microsoft's Playwright Model Context Protocol server gives AI agents full browser automation, scraping, and visual testing capabilities. Agents can navigate pages, click buttons, fill forms, take full-page screenshots, and extract rendered DOM elements.",
        "capabilities": [
            "Automate browser sessions to interact with client-side JavaScript applications and SPA dashboards.",
            "Capture screenshots and visual artifacts to verify UI layout and responsiveness during development.",
            "Scrape rendered DOM content behind interactive logins, dropdowns, and paginated tables.",
            "Run automated end-to-end user flows directly from natural language specifications."
        ],
        "prompts": [
            "Navigate to our staging URL, log in with test credentials, and take a screenshot of the dashboard.",
            "Inspect the payment checkout page and check if any network requests return 4xx or 5xx status codes.",
            "Extract the table rows from the active page and format them into a clean markdown table."
        ]
    },
    "ChromeDevTools/chrome-devtools-mcp": {
        "summary": "Official Chrome DevTools Protocol MCP server. Allows AI agents and coding assistants to inspect live web apps, evaluate JavaScript in page contexts, profile performance, capture network traces, and debug DOM mutations directly.",
        "capabilities": [
            "Inspect live DOM trees, CSS styles, and computed layout properties in Google Chrome.",
            "Evaluate JavaScript expressions in the console context of active browser tabs.",
            "Record and analyze Chrome performance timelines, network waterfalls, and Core Web Vitals.",
            "Automate headless Chrome testing with deep DevTools telemetry."
        ],
        "prompts": [
            "Open Chrome DevTools, inspect the hero element on localhost:3000, and check why its margin is collapsing.",
            "Capture the network trace during page load and identify which third-party scripts block the main thread.",
            "Evaluate the window.__INITIAL_STATE__ object and print the authenticated user session details."
        ]
    },
    "upstash/context7": {
        "summary": "Context-aware caching and semantic retrieval server powered by Upstash serverless Redis and Vector. Enables AI agents to store, search, and recall high-dimensional embeddings and conversation contexts with sub-millisecond latency.",
        "capabilities": [
            "Store and query high-dimensional vector embeddings without managing dedicated vector infrastructure.",
            "Cache LLM responses and tool outputs with configurable TTL to reduce API costs and latency.",
            "Provide fast semantic lookup for documentation, code snippets, and customer chat history.",
            "Scale seamlessly from local development to production workloads with serverless architecture."
        ],
        "prompts": [
            "Store this project's API documentation chunks into the Upstash vector index.",
            "Perform a semantic search for 'OAuth token expiration handling' across our cached knowledge base.",
            "Retrieve the cached response for this frequent query instead of calling the frontier model."
        ]
    },
    "BerriAI/litellm": {
        "summary": "LiteLLM provides a standardized OpenAI-compatible proxy interface to call 100+ LLMs (Anthropic, Bedrock, Vertex AI, Ollama, Groq, Azure). When used as an MCP server, it gives agents dynamic multi-model routing, load balancing, fallback logic, and spend tracking.",
        "capabilities": [
            "Route agent tasks dynamically to 100+ LLM providers using one unified API interface.",
            "Implement automatic fallbacks and retries when a model provider experiences rate limits or downtime.",
            "Track per-user and per-project token usage, spend limits, and latency metrics across all models.",
            "Integrate local models (Ollama, vLLM) alongside frontier commercial models effortlessly."
        ],
        "prompts": [
            "Route this classification task to Claude 3.5 Haiku, falling back to Gemini 1.5 Flash if rate limited.",
            "Check current monthly token spend and budget usage across all connected LLM providers.",
            "Test model response latency across Bedrock, Azure OpenAI, and Anthropic for our prompt."
        ]
    },
    "mudler/LocalAI": {
        "summary": "LocalAI is a free, open-source, self-hosted alternative to OpenAI that runs local LLMs, audio transcription, image generation, and embeddings on consumer-grade hardware without requiring cloud GPUs.",
        "capabilities": [
            "Run local LLM inference completely offline with zero telemetry or data exfiltration.",
            "Generate local embeddings, audio transcriptions (Whisper), and image generations (Stable Diffusion).",
            "Expose an OpenAI-compatible REST API directly to MCP clients like Claude and Cursor.",
            "Run models efficiently on CPU and Apple Silicon with quantization support."
        ],
        "prompts": [
            "Generate embeddings for this document using the local BGE embedding model.",
            "Transcribe this audio recording using the local Whisper model running on LocalAI.",
            "Run this prompt against our local Llama 3 model without sending data to external APIs."
        ]
    },
    "github/github-mcp-server": {
        "summary": "Official GitHub Model Context Protocol server. Connects AI developer tools directly to GitHub repositories, pull requests, issues, commits, branches, and code search.",
        "capabilities": [
            "Search repositories, code, and commit histories across personal or organization GitHub accounts.",
            "Inspect pull requests, review diffs, check CI check-runs, and post review comments directly.",
            "Create, update, and triage GitHub issues with automated labels and assignees.",
            "Fork, branch, and push commits directly through AI agent tool calls."
        ],
        "prompts": [
            "List open pull requests assigned to me and summarize their review status and CI results.",
            "Search our organization's repos for any open issues mentioning 'CVE-2026' or 'memory leak'.",
            "Read pull request #45, review the diff against main, and suggest improvements in code comments."
        ]
    },
    "PrefectHQ/fastmcp": {
        "summary": "FastMCP by Prefect is the standard high-level Python framework for building Model Context Protocol servers with minimal boilerplate, automatic schema generation, and built-in SSE/stdio transport support.",
        "capabilities": [
            "Build robust MCP servers in Python using simple `@mcp.tool()` and `@mcp.resource()` decorators.",
            "Automatically generate OpenAPI-compliant JSON schemas and type validations from Python type hints.",
            "Deploy servers effortlessly with built-in stdio, SSE (Server-Sent Events), and FastAPI integrations.",
            "Test and debug MCP tools locally before deploying to production AI agents."
        ],
        "prompts": [
            "Generate a FastMCP Python server that exposes our internal SQL query tool with strict validation.",
            "Add an SSE endpoint to our FastMCP server so remote Claude Desktop instances can connect over HTTP.",
            "Inspect the registered tools and their generated JSON schemas on this FastMCP server."
        ]
    },
    "danny-avila/LibreChat": {
        "summary": "LibreChat is an open-source AI chat platform that brings multimodal AI, code execution, artifacts, and Model Context Protocol servers into a single unified web workspace.",
        "capabilities": [
            "Connect multiple Model Context Protocol servers to a single web-based chat interface.",
            "Switch seamlessly between Anthropic Claude, OpenAI, Google Gemini, and local LLMs.",
            "Manage enterprise user workspaces, granular access permissions, and shared prompt templates.",
            "Inspect artifact visualizations and execution logs side-by-side with chat turns."
        ],
        "prompts": [
            "Enable the GitHub and Postgres MCP tools for this conversation session in LibreChat.",
            "Compare model responses side-by-side between Claude 3.5 Sonnet and Gemini 1.5 Pro.",
            "Review the tool execution history from our last automated data extraction task."
        ]
    },
    "assafelovic/gpt-researcher": {
        "summary": "Autonomous AI research agent that scrapes, filters, and aggregates information from 20+ web sources to generate comprehensive, cited technical research reports.",
        "capabilities": [
            "Formulate multi-angle search queries and autonomously crawl top search results.",
            "Filter out marketing fluff, paywalls, and duplicate text to extract core technical facts.",
            "Compile academic-style research reports complete with formal citations and markdown tables.",
            "Operate continuously in the background to monitor breaking industry developments."
        ],
        "prompts": [
            "Research the current state of Model Context Protocol adoption in enterprise environments and compile a cited report.",
            "Investigate recent architectural improvements in speculative decoding for LLMs.",
            "Summarize the competitive landscape for open-source vector databases in 2026."
        ]
    },
    "czlonkowski/n8n-mcp": {
        "summary": "A dedicated Model Context Protocol server for n8n that exposes workflow management, workflow triggering, and execution inspection tools to AI assistants like Claude and Cursor.",
        "capabilities": [
            "Discover all workflows and credentials configured in your n8n workspace.",
            "Trigger workflows synchronously or asynchronously with custom JSON payloads.",
            "Fetch workflow execution history, node outputs, and error stack traces.",
            "Manage webhook listeners and scheduled cron executions from natural language."
        ],
        "prompts": [
            "List all workflows related to Slack notifications and check their active status.",
            "Execute the 'Weekly Data Backup' workflow in n8n and notify me of the result.",
            "Find any workflow executions that encountered an error in the past 24 hours."
        ]
    },
    "GLips/Figma-Context-MCP": {
        "summary": "Connects Figma design files and component contexts directly into Claude and Cursor for seamless design-to-code development workflows.",
        "capabilities": [
            "Inspect Figma frames, component hierarchies, auto-layout settings, and CSS properties.",
            "Translate Figma UI designs into clean Tailwind, React, or Vue component code.",
            "Verify that implemented frontend components accurately match design tokens and spacing.",
            "Extract color schemes, typography hierarchies, and SVG icons directly into your IDE."
        ],
        "prompts": [
            "Inspect the Figma frame for the navigation bar and generate a responsive React component with Tailwind CSS.",
            "Check the color palette and typography tokens from our Figma design system.",
            "Compare our implemented button component with the Figma design specification for visual deviations."
        ]
    },
    "activepieces/activepieces": {
        "summary": "Open-source, self-hostable workflow automation engine. When used as an MCP server, it gives AI agents access to over 200 open-source integration pieces across developer and business services.",
        "capabilities": [
            "Execute workflows across popular developer services, marketing tools, and cloud infrastructure.",
            "Build resilient automated triggers with human-in-the-loop approvals.",
            "Maintain full data privacy through self-hosted Docker deployments.",
            "Extend capabilities with custom TypeScript integration pieces."
        ],
        "prompts": [
            "Trigger the Activepieces flow to sync new GitHub issues to our internal tracker.",
            "List available integration pieces and their supported trigger actions.",
            "Create an automated alert when customer signup volume drops below threshold."
        ]
    },
    "1Panel-dev/MaxKB": {
        "summary": "Ready-to-use knowledge base Q&A system based on large language models. Allows AI assistants to ingest documentation and perform accurate retrieval-augmented generation.",
        "capabilities": [
            "Ingest PDF, Word, and markdown documentation with intelligent semantic chunking.",
            "Perform hybrid vector and full-text keyword retrieval across internal docs.",
            "Integrate enterprise knowledge bases directly into Claude and Cursor chats.",
            "Manage fine-grained document access permissions across team roles."
        ],
        "prompts": [
            "Query MaxKB for our company's remote work policy regarding equipment reimbursement.",
            "Index our latest architecture specifications into the MaxKB knowledge base.",
            "Retrieve technical troubleshooting steps for database connection timeout errors."
        ]
    },
    "triggerdotdev/trigger.dev": {
        "summary": "Background jobs and workflow automation framework for TypeScript developers. Exposes job scheduling, background task dispatching, and durable execution to MCP agents.",
        "capabilities": [
            "Dispatch long-running background tasks without HTTP timeout restrictions.",
            "Monitor real-time task execution logs and retry failed runs automatically.",
            "Schedule cron jobs and delayed event triggers directly from agent commands.",
            "Maintain end-to-end type safety between AI tool calls and backend tasks."
        ],
        "prompts": [
            "Trigger the 'Nightly Data Ingestion' background job in Trigger.dev and monitor its progress.",
            "Check the error logs for the last failed background task execution.",
            "Schedule a recurring background task to clean up temporary storage buckets."
        ]
    },
    "googleapis/mcp-toolbox": {
        "summary": "Google's official Model Context Protocol toolbox providing native integrations with Google Cloud Platform, BigQuery, Cloud Storage, and developer APIs.",
        "capabilities": [
            "Query BigQuery datasets and inspect schemas using natural language.",
            "Manage Cloud Storage buckets and upload/download objects through agent tools.",
            "Inspect Google Cloud resources and cloud billing telemetry.",
            "Enforce IAM role boundaries and service account security."
        ],
        "prompts": [
            "Run a query against our BigQuery telemetry dataset to count daily active sessions.",
            "List the files stored in our primary Cloud Storage backup bucket.",
            "Inspect the IAM permissions associated with our active service account."
        ]
    },
    "casdoor/casdoor": {
        "summary": "UI-first Identity and Access Management (IAM) and Single Sign-On (SSO) platform supporting OAuth 2.0, OIDC, SAML, and WebAuthn.",
        "capabilities": [
            "Inspect user directories, manage roles, and audit access permissions.",
            "Verify OAuth 2.0 authentication flows and JWT token structures.",
            "Automate user provisioning and security compliance auditing.",
            "Configure third-party social logins and enterprise SAML connectors."
        ],
        "prompts": [
            "List all users with administrative roles in Casdoor and check their MFA status.",
            "Verify that the OAuth 2.0 redirect URI for our application is properly configured.",
            "Audit recent authentication log failures and flag suspicious IP addresses."
        ]
    },
    "kubeshark/kubeshark": {
        "summary": "API traffic analyzer and observability tool for Kubernetes. Provides deep protocol inspection for HTTP, gRPC, and WebSocket traffic across cluster pods.",
        "capabilities": [
            "Capture and inspect live network traffic between Kubernetes pods in real time.",
            "Troubleshoot microservice communication failures and latency bottlenecks.",
            "Audit API payloads and headers for security and protocol compliance.",
            "Filter network traffic by Kubernetes namespace, pod, or service labels."
        ],
        "prompts": [
            "Capture HTTP traffic to the auth-service pod and inspect any 500 error responses.",
            "Analyze gRPC message throughput between our frontend and backend microservices.",
            "Check for unencrypted HTTP traffic carrying sensitive authorization headers."
        ]
    },
    "zylon-ai/private-gpt": {
        "summary": "Production-ready 100% private, local AI agent solution that enables interaction with your documents using local LLMs with zero data leaks.",
        "capabilities": [
            "Query local documents completely offline without third-party API exposure.",
            "Run high-accuracy RAG over PDFs, text, and markdown files.",
            "Integrate with local Ollama or llama.cpp backends effortlessly.",
            "Ensure full regulatory compliance with strict on-premise execution."
        ],
        "prompts": [
            "Ask PrivateGPT to search our internal design doc for security guidelines.",
            "Index the local compliance folder and verify all documents are processed.",
            "Summarize the legal contract terms without sending any text to external APIs."
        ]
    },
    "koala73/worldmonitor": {
        "summary": "Global geopolitical and infrastructure intelligence monitor aggregating real-time flight, maritime, satellite, and conflict data feeds.",
        "capabilities": [
            "Stream real-time global event telemetry and maritime/air traffic signals.",
            "Analyze geospatial anomaly indicators across critical supply chains.",
            "Query open-source intelligence feeds with natural language queries.",
            "Monitor critical shipping routes and infrastructure disruptions."
        ],
        "prompts": [
            "Check active maritime congestion near major global shipping straits.",
            "Summarize high-priority geopolitical conflict indicators reported in the last 24 hours.",
            "Track flight telemetry anomalies near the specified regional airspace."
        ]
    },
    "bytedance/UI-TARS-desktop": {
        "summary": "Vision-language GUI agent that operates desktop interfaces through visual perception, mouse clicks, keyboard inputs, and window management.",
        "capabilities": [
            "Execute desktop computer tasks by interpreting screen visuals and GUI elements.",
            "Automate complex multi-window workflows across native desktop applications.",
            "Bridge visual UI automation directly into Model Context Protocol agents.",
            "Operate desktop applications that lack public APIs or CLI interfaces."
        ],
        "prompts": [
            "Open the terminal application, navigate to the project directory, and start the development server.",
            "Take a screenshot of the active application window and identify all clickable buttons.",
            "Fill out the desktop spreadsheet with the parsed financial values."
        ]
    },
    "sansan0/TrendRadar": {
        "summary": "Real-time multi-platform trend monitoring engine tracking trending topics across GitHub, Hacker News, Twitter/X, and tech forums.",
        "capabilities": [
            "Monitor breakout developer tools, trending repositories, and open-source topics.",
            "Aggregate developer sentiment and discussion volume across multiple platforms.",
            "Alert AI agents when specific keywords or topics spike in volume.",
            "Track rising stars and velocity among new AI and MCP repositories."
        ],
        "prompts": [
            "What are the top 5 trending open-source AI projects on GitHub today?",
            "Search recent Hacker News discussions for reactions to the latest Model Context Protocol release.",
            "Identify developer sentiment regarding recent TypeScript framework updates."
        ]
    },
    "headroomlabs-ai/headroom": {
        "summary": "Intelligent context compression and dynamic token budgeting engine for large language models and multi-turn agent conversations.",
        "capabilities": [
            "Compress long prompt histories while preserving critical reasoning facts and code snippets.",
            "Reduce LLM token usage and latency without sacrificing task accuracy.",
            "Dynamically allocate token budgets across multi-agent tool calling sequences.",
            "Eliminate redundant conversational tokens to optimize API costs."
        ],
        "prompts": [
            "Compress this 80,000 token conversation transcript to under 8,000 tokens while preserving code snippets.",
            "Analyze token allocation across our agent's recent tool calls and identify redundancy.",
            "Budget token usage for a planned 10-step multi-agent research workflow."
        ]
    },
    "HKUDS/nanobot": {
        "summary": "Ultra-lightweight autonomous agent framework optimized for edge devices and low-resource environments with fast tool calling.",
        "capabilities": [
            "Run autonomous agent loops with minimal memory footprint and zero external dependencies.",
            "Execute rapid local tool calling cycles with quantized small language models.",
            "Integrate edge sensor telemetry into MCP-compliant workflows.",
            "Deploy autonomous bots on constrained hardware like Raspberry Pi or local containers."
        ],
        "prompts": [
            "Initialize a lightweight agent loop to monitor local system resources every 30 seconds.",
            "Execute the automated cleanup task using minimal token overhead.",
            "Collect sensor readings and format them as an MCP resource payload."
        ]
    },
    "modelcontextprotocol/python-sdk": {
        "summary": "The official Python SDK for the Model Context Protocol, providing the core abstractions for building and consuming MCP servers and clients.",
        "capabilities": [
            "Implement custom MCP servers with full stdio and SSE transport support.",
            "Create MCP clients that connect to and orchestrate third-party servers.",
            "Validate JSON-RPC message schemas and lifecycle management.",
            "Integrate asynchronous Python tools and resources with strict typing."
        ],
        "prompts": [
            "Create a minimal Python MCP server using the official SDK that exposes a calculator tool.",
            "Connect an MCP client to a local stdio server and list its available resources.",
            "Debug an SSE connection handshake error between client and server."
        ]
    },
    "D4Vinci/Scrapling": {
        "summary": "Undetectable, lightning-fast web scraping engine designed to bypass anti-bot protections and extract structured web content effortlessly.",
        "capabilities": [
            "Scrape dynamic web pages while bypassing advanced anti-bot challenges and fingerprinting.",
            "Extract structured data elements with fast CSS selectors and XPath queries.",
            "Feed clean web content directly into AI agent reasoning loops.",
            "Handle cookie rotation and automated proxy management seamlessly."
        ],
        "prompts": [
            "Scrape the pricing table from the target website and return clean JSON.",
            "Fetch the latest articles from the tech blog and extract the title, author, and content.",
            "Extract product specifications from the e-commerce catalogue without triggering blocks."
        ]
    }
}

# Domain-specific capabilities for all other servers by category
CATEGORY_CAPABILITIES = {
    "AI/LLM": [
        "Connect external AI models, providers, and orchestration layers to your local assistant.",
        "Perform structured output generation, multi-model consensus, and agent prompt chaining.",
        "Query context embeddings, vector retrieval, and long-term conversation buffers."
    ],
    "Code/Dev Tools": [
        "Inspect, lint, and edit local repositories directly through AI agent tool calls.",
        "Execute automated test suites, build pipelines, and parse compiler errors.",
        "Generate AST code modifications and refactor legacy dependencies safely."
    ],
    "Database": [
        "Query database schemas, inspect table structures, and run analytical SQL queries via natural language.",
        "Stream query results directly to LLMs without exposing raw production credentials.",
        "Automate schema migrations, database index auditing, and slow-query diagnostics."
    ],
    "API Integration": [
        "Connect AI agents to third-party SaaS platforms, REST endpoints, and webhooks.",
        "Automate repetitive workflow executions, issue tracking, and ticket updates.",
        "Perform authenticated read/write operations across external developer services."
    ],
    "Browser/Web": [
        "Automate browser actions, page scraping, and dynamic DOM interaction via AI.",
        "Take visual UI screenshots and perform end-to-end regression verification.",
        "Extract structured JSON data from JavaScript-heavy web applications."
    ],
    "Security": [
        "Scan source code and third-party dependencies for common vulnerability patterns.",
        "Audit tool invocation permissions, network access, and sandbox configurations.",
        "Generate automated TRiSM security reports for MCP server deployments."
    ],
    "Memory/Knowledge": [
        "Provide persistent memory across multiple AI chat sessions and projects.",
        "Index local markdown notes, code documentation, and organizational knowledge bases.",
        "Perform hybrid semantic and BM25 keyword search over personal workspaces."
    ],
    "Devops": [
        "Monitor container health, inspect Kubernetes cluster state, and stream service logs.",
        "Automate deployment workflows, rollbacks, and infrastructure provisioning via chat.",
        "Diagnose runtime issues, networking bottlenecks, and configuration drift."
    ],
    "Finance": [
        "Fetch real-time financial market data, crypto prices, and order book depth.",
        "Perform automated portfolio risk analysis and financial modeling directly in chat.",
        "Audit smart contracts, wallet transactions, and ledger accounting balances."
    ],
    "Media": [
        "Process, resize, and convert images, audio, and video files via AI commands.",
        "Extract metadata, transcribe speech-to-text, and parse media assets.",
        "Chain media generation pipelines with local post-processing scripts."
    ],
    "Communication": [
        "Send notifications, alerts, and messages across Slack, Discord, Telegram, or email.",
        "Facilitate collaborative agent workflows and autonomous notification dispatching.",
        "Monitor communication channels for critical incidents and team mentions."
    ],
    "File System": [
        "Provide controlled, sandboxed file reading and writing for AI coding assistants.",
        "Search files by name, path patterns, or regular expressions across nested projects.",
        "Manage project directories, configuration files, and temporary artifacts safely."
    ],
    "Search": [
        "Retrieve live web search results and technical documentation directly into LLM context.",
        "Extract clean, readable article content without ad scripts or popups.",
        "Ground AI answers with citations from verified external sources."
    ],
    "Other": [
        "Expose custom domain tools and command-line utilities to Model Context Protocol clients.",
        "Enable autonomous agent execution for specialized developer workflows.",
        "Bridge proprietary APIs and data feeds into Claude Desktop, Cursor, and IDEs."
    ]
}

# Domain-specific example prompts by category
CATEGORY_PROMPT_TEMPLATES = {
    "AI/LLM": (
        "Route this complex analysis task to the connected model and return a structured JSON report.",
        "Compare the reasoning outputs between two connected models and highlight any discrepancies."
    ),
    "Code/Dev Tools": (
        "Review recent commits in this repository, run the test suite, and highlight performance bottlenecks.",
        "Search for functions that don't have unit tests and generate test cases for them."
    ),
    "Database": (
        "Inspect the schema for the main tables and show the top 10 records by activity.",
        "Run an EXPLAIN ANALYZE on our slow query and suggest index improvements."
    ),
    "API Integration": (
        "Trigger the customer synchronization workflow and alert me if any records fail validation.",
        "List all recent webhook events and show the payload for the latest failed event."
    ),
    "Browser/Web": (
        "Navigate to the target dashboard, capture a full-page screenshot, and extract all table rows.",
        "Check if the login form displays proper validation errors when submitted empty."
    ),
    "Security": (
        "Scan the connected repository for hardcoded API keys or vulnerable dependencies.",
        "Audit the permissions of all connected MCP tools and flag potential injection risks."
    ),
    "Memory/Knowledge": (
        "Search our project notes for previous architecture decisions regarding token authentication.",
        "Save this design summary to our long-term memory graph for future reference."
    ),
    "Devops": (
        "Check the status of all running Docker containers and alert me of any non-zero exit codes.",
        "Fetch the last 50 lines of logs from the production web service and check for errors."
    ),
    "Finance": (
        "Retrieve the current BTC/USD and ETH/USD market depth and calculate the 24h spread.",
        "Analyze my portfolio holdings and summarize value-at-risk under a 10% market drop."
    ),
    "Media": (
        "Transcribe this audio recording and format the key action items into a markdown list.",
        "Convert all PNG images in this directory to WebP format with 85% quality."
    ),
    "Communication": (
        "Send a notification to the #releases Slack channel that deployment v2.4.0 is live.",
        "Summarize the last 10 messages in the urgent support thread."
    ),
    "File System": (
        "Find all files in this project that have been modified in the last 24 hours.",
        "Read the contents of config.json and check if the database host is configured."
    ),
    "Search": (
        "Search the web for the latest documentation on Model Context Protocol SSE transports.",
        "Find recent technical discussions regarding Python 3.13 GIL removal."
    ),
    "Other": (
        "Use the connected tools to inspect the environment and execute the requested task.",
        "List the available commands on this server and describe what each tool does."
    )
}


def generate_server_overview_html(server):
    """
    Builds a rich, SEO-optimized 'What This Server Does & Key Capabilities' section
    for server detail pages, including curated guides for top repos, category-driven
    capability bullets, copyable example agent prompts, and compatible AI client badges.
    """
    repo = server["repo"]
    name = server["name"]
    desc = server.get("description") or "An MCP server."
    cat = server.get("category", "Other")

    curated = CURATED_SERVER_DOCS.get(repo)
    if curated:
        summary_text = curated["summary"]
        caps = curated["capabilities"]
        prompts = curated["prompts"]
    else:
        summary_text = f"The <strong>{escape(name)}</strong> Model Context Protocol (MCP) server provides seamless integration between AI assistants (such as Claude Desktop, Cursor, and Claude Code) and {escape(desc.rstrip('.'))}. By connecting this server, your AI agent gains specialized capabilities to inspect, query, and automate tasks within the {escape(cat)} domain."
        caps = CATEGORY_CAPABILITIES.get(cat, CATEGORY_CAPABILITIES["Other"])
        prompts = CATEGORY_PROMPT_TEMPLATES.get(cat, CATEGORY_PROMPT_TEMPLATES["Other"])

    caps_html = "".join(
        f'<li style="margin-bottom:8px;display:flex;align-items:flex-start;gap:8px">'
        f'<span style="color:var(--accent);font-weight:700">✓</span> '
        f'<span>{escape(c)}</span></li>'
        for c in caps
    )

    prompts_html = ""
    for p in prompts[:2]:
        clean_p = p.strip('"')
        escaped_js = clean_p.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
        prompts_html += f"""
        <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:12px 16px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;gap:12px">
            <span style="font-family:var(--mono);font-size:0.85rem;color:var(--text);word-break:break-word">"{escape(clean_p)}"</span>
            <button onclick="navigator.clipboard.writeText('{escaped_js}');this.textContent='Copied!';setTimeout(()=>this.textContent='Copy',2000)" style="background:var(--bg-card);border:1px solid var(--border);color:var(--text-muted);font-size:0.75rem;padding:4px 10px;border-radius:6px;cursor:pointer;white-space:nowrap;transition:all 0.2s">Copy</button>
        </div>"""

    return f"""
    <div class="detail-section server-overview-card" style="background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:24px;margin-bottom:32px">
        <h2 style="font-size:1.15rem;font-weight:800;color:var(--text);margin-top:0;margin-bottom:12px;display:flex;align-items:center;gap:8px">
            ⚡ What This Server Does &amp; Key Capabilities
        </h2>
        <p style="color:var(--text-muted);font-size:0.95rem;line-height:1.7;margin-bottom:20px">
            {summary_text}
        </p>

        <h3 style="font-size:0.85rem;text-transform:uppercase;letter-spacing:0.05em;color:var(--text-dim);font-weight:700;margin-bottom:12px">
            Core Agent Capabilities
        </h3>
        <ul style="list-style:none;padding:0;margin:0 0 24px 0;font-size:0.9rem;color:var(--text)">
            {caps_html}
        </ul>

        <h3 style="font-size:0.85rem;text-transform:uppercase;letter-spacing:0.05em;color:var(--text-dim);font-weight:700;margin-bottom:12px">
            💡 Example Prompts to Ask Your AI Agent
        </h3>
        <p style="color:var(--text-dim);font-size:0.82rem;margin-bottom:12px">
            Once installed in Claude Desktop or Cursor, try asking your assistant:
        </p>
        <div style="margin-bottom:20px">
            {prompts_html}
        </div>

        <h3 style="font-size:0.85rem;text-transform:uppercase;letter-spacing:0.05em;color:var(--text-dim);font-weight:700;margin-bottom:10px">
            Compatible AI Clients
        </h3>
        <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center">
            <span style="display:inline-flex;align-items:center;gap:6px;padding:4px 10px;background:rgba(123,97,255,0.1);border:1px solid rgba(123,97,255,0.25);border-radius:6px;font-size:0.8rem;color:#bca7ff;font-weight:600">🟣 Claude Desktop</span>
            <span style="display:inline-flex;align-items:center;gap:6px;padding:4px 10px;background:rgba(45,217,224,0.1);border:1px solid rgba(45,217,224,0.25);border-radius:6px;font-size:0.8rem;color:#2dd9e0;font-weight:600">⚡ Cursor IDE</span>
            <span style="display:inline-flex;align-items:center;gap:6px;padding:4px 10px;background:rgba(255,255,255,0.06);border:1px solid var(--border);border-radius:6px;font-size:0.8rem;color:var(--text);font-weight:600">💻 Claude Code CLI</span>
            <span style="display:inline-flex;align-items:center;gap:6px;padding:4px 10px;background:rgba(255,255,255,0.06);border:1px solid var(--border);border-radius:6px;font-size:0.8rem;color:var(--text);font-weight:600">🌊 Windsurf</span>
            <span style="display:inline-flex;align-items:center;gap:6px;padding:4px 10px;background:rgba(255,255,255,0.06);border:1px solid var(--border);border-radius:6px;font-size:0.8rem;color:var(--text);font-weight:600">🤖 Gemini CLI</span>
        </div>
    </div>
    """
