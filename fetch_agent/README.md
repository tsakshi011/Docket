# Docket Study-Resource Agent for Fetch.ai Agentverse

An AI agent that finds the best free study resources for any university course, discoverable via [ASI:One](https://asi1.ai) through the [Agentverse](https://agentverse.ai) marketplace.

## What it does

Users ask for study resources in natural language (e.g., "Find resources for Organic Chemistry") and the agent:

1. Uses Tavily web search to find real, verified URLs across YouTube, MIT OCW, Coursera, Khan Academy, etc.
2. Runs a ReAct-style reasoning loop (Groq LLM) to decide which searches to make and curate results
3. Returns formatted resources organized by topic with study tips

## Architecture

```
ASI:One Chat  ──>  Agentverse (hosted)  ──>  Docket Agent
                                                  │
                                          ┌───────┴────────┐
                                          │  Chat Protocol  │
                                          │  (mandatory)     │
                                          └───────┬────────┘
                                                  │
                                          ┌───────┴────────┐
                                          │  ReAct Loop     │
                                          │  (Groq LLM)     │
                                          └───────┬────────┘
                                                  │
                              ┌────────────┬──────┴──────┬──────────────┐
                              │            │             │              │
                        search_web  search_youtube  search_academic  search_practice
                              │            │             │              │
                              └────────────┴──────┬──────┴──────────────┘
                                                  │
                                            Tavily API
```

## Prerequisites

- [Groq API key](https://console.groq.com/keys) (free tier works)
- [Tavily API key](https://tavily.com) (free tier: 1,000 searches/month)
- [Agentverse account](https://agentverse.ai) (free)

## Setup (Hosted Agent — Recommended)

This is the easiest approach: the agent runs on Agentverse's infrastructure — no local setup needed.

### 1. Create a Hosted Agent on Agentverse

1. Go to [agentverse.ai](https://agentverse.ai) → **My Agents** → **+ Launch an Agent**
2. Select **Create an Agent** → **Blank** template
3. Name it `Docket Study Resources`
4. Assign keywords: `study`, `resources`, `education`
5. Click **Launch Agent**

### 2. Paste the agent code

1. Go to the **Build** tab in the Agent Editor
2. Copy the entire contents of [`agent_hosted.py`](./agent_hosted.py) and paste it into the editor
3. Click **Save** and then **Start** the agent

### 3. Add API key secrets

1. Go to the agent's **Secrets** tab (or Settings → Secrets)
2. Add two secrets:
   - `GROQ_API_KEY` → your Groq API key (get one at https://console.groq.com/keys)
   - `TAVILY_API_KEY` → your Tavily API key (get one at https://tavily.com)

### 4. Set up your Agent Profile for discoverability

1. Go to the agent's **Dashboard** or **Profile** section
2. Set a descriptive **name**: `Docket Study Resources`
3. Set a **handle**: e.g., `@docket-study-resources`
4. Write a **description**:
   > I find the best free study resources for any university course. Tell me a course name (e.g., "Organic Chemistry", "CS 161 Data Structures", "Civil Procedure") and I'll search YouTube, MIT OCW, Coursera, Khan Academy, and more to curate personalized study materials organized by topic.
5. Add a **README** following [Agentverse README Guidelines](https://docs.agentverse.ai/documentation/agent-discovery/readme-guidelines)
6. Click **Save**

### 5. Test via ASI:One Chat

1. In the Agent Profile page, click **Chat with Agent**
2. Or go to [asi1.ai](https://asi1.ai) and search for your agent by name
3. Type a course name, e.g.: `Find study resources for Linear Algebra`
4. The agent will search the web and return curated resources

### 6. Get your deliverable URLs

After testing, collect these for your hackathon submission:

- **ASI:One Chat session URL**: Click "Share" in your ASI:One chat to get a URL like:
  `https://asi1.ai/shared-chat/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- **Agentverse agent URL**: Found in your Agent Profile page:
  `https://agentverse.ai/agents/details/<your-agent-address>/profile`
- **GitHub repo URL**: `https://github.com/tsakshi011/Docket`

## Alternative: Local Agent (Advanced)

If you prefer to run the agent locally and connect via mailbox, use `agent.py` instead:

```bash
cd backend && pip install -e . && pip install uagents
export GROQ_API_KEY="gsk_..."
export TAVILY_API_KEY="tvly-..."
export AGENT_SEED="your-unique-secret-seed-phrase"
python fetch_agent/agent.py
```

Then connect the mailbox via the Agent Inspector link in the terminal output.

> **Note:** Local agents require you to fix macOS SSL certificates first:
> ```bash
> export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")
> ```

## How it works

### Chat Protocol (mandatory requirement)

The agent implements the Fetch.ai Chat Protocol spec:

1. Receives `ChatMessage` from ASI:One
2. Sends `ChatAcknowledgement` immediately
3. Extracts user text from message content
4. Runs the resource search pipeline
5. Returns `ChatMessage` with `TextContent` (results) + `EndSessionContent`

### ReAct Resource Search

The agent uses a ReAct (Reasoning + Acting) loop:

1. **Thought**: The LLM decides what information is needed
2. **Action**: Calls a search tool (Tavily-powered)
3. **Observation**: Receives search results
4. **Repeat** until enough resources are found (max 4 turns)
5. **Finish**: Returns structured, formatted results

### Token Efficiency

- Uses `llama-3.1-8b-instant` (cheap, fast)
- Sliding context window keeps only last 3 tool results
- 3 search results per query, truncated to 1500 chars
- Total: ~6K tokens per query (~16 queries/day on Groq free tier)

## Files

| File | Description |
|------|-------------|
| `agent_hosted.py` | **Self-contained hosted agent** — paste into Agentverse Editor. Uses `requests` for Tavily API (no external dependencies). |
| `agent.py` | Local agent version — imports from Docket backend, connects via mailbox. |
| `README.md` | This file. |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Agent not responding | Check that both API key secrets are set in the Secrets tab |
| Rate limit errors (429) | Wait a few minutes; the agent uses the 8B model to stay within free-tier limits |
| Agent not appearing on ASI:One | Make sure the agent is running (green status) and profile is filled out |
| No search results | Check that Tavily API key is valid and has remaining quota |
