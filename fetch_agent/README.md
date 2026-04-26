# Docket Study-Resource Agent for Fetch.ai Agentverse

An AI agent that finds the best free study resources for any university course, discoverable via [ASI:One](https://asi1.ai) through the [Agentverse](https://agentverse.ai) marketplace.

## What it does

Users ask for study resources in natural language (e.g., "Find resources for Organic Chemistry") and the agent:

1. Uses Tavily web search to find real, verified URLs across YouTube, MIT OCW, Coursera, Khan Academy, etc.
2. Runs a ReAct-style reasoning loop (Groq LLM) to decide which searches to make and curate results
3. Returns formatted resources organized by topic with study tips

## Architecture

```
ASI:One Chat  ──>  Agentverse (mailbox)  ──>  This Agent
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

- Python 3.11+
- [Groq API key](https://console.groq.com/keys) (free tier works)
- [Tavily API key](https://tavily.com) (free tier: 1,000 searches/month)
- [Agentverse account](https://agentverse.ai) (free)

## Setup

### 1. Install dependencies

```bash
cd backend
pip install -e .
pip install uagents
```

### 2. Set environment variables

```bash
export GROQ_API_KEY="gsk_..."
export TAVILY_API_KEY="tvly-..."
export AGENT_SEED="your-unique-secret-seed-phrase"   # generates your agent address
export AGENT_PORT=8001                                # optional, default 8001
```

> **Important:** The `AGENT_SEED` determines your agent's address. Use a unique, memorable phrase and keep it consistent — changing it creates a new agent identity.

### 3. Run the agent

```bash
python fetch_agent/agent.py
```

You should see output like:

```
INFO:     [docket-study-resources]: Starting agent with address: agent1q...
INFO:     [docket-study-resources]: Agent inspector available at https://agentverse.ai/inspect/?uri=http%3A//127.0.0.1%3A8001&address=agent1q...
INFO:     [docket-study-resources]: Starting server on http://0.0.0.0:8001
INFO:     [docket-study-resources]: Starting mailbox client for https://agentverse.ai
```

### 4. Connect to Agentverse (mailbox)

1. Click the **Agent inspector** link from the terminal output
2. Click **Connect** and select **Mailbox**
3. Your agent is now registered on the Almanac and can receive messages from ASI:One

### 5. Set up your Agent Profile

1. In the Inspector, click **Agent Profile**
2. Set a descriptive name: e.g., `Docket Study Resources`
3. Set a handle: e.g., `@docket-study-resources`
4. Write a description:
   > I find the best free study resources for any university course. Tell me a course name (e.g., "Organic Chemistry", "CS 161 Data Structures", "Civil Procedure") and I'll search YouTube, MIT OCW, Coursera, Khan Academy, and more to curate personalized study materials organized by topic.
5. Click **Save**

### 6. Test via ASI:One Chat

1. In the Agent Profile page, click **Chat with Agent**
2. Or go to [asi1.ai](https://asi1.ai) and search for your agent
3. Type a course name, e.g.: "Find study resources for Linear Algebra"
4. The agent will search and return curated resources

### 7. Get your deliverable URLs

After testing, collect these for your hackathon submission:

- **ASI:One Chat session URL**: Click "Share" in your ASI:One chat to get a URL like:
  `https://asi1.ai/shared-chat/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- **Agentverse agent URL**: Found in your Agent Profile page:
  `https://agentverse.ai/agents/details/<your-agent-address>/profile`
- **GitHub repo URL**: `https://github.com/tsakshi011/Docket`

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
- Total: ~6K tokens per query (~16 queries/day on free tier)

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `GROQ_API_KEY is not set` | Export the env var before running |
| `TAVILY_API_KEY is not set` | Export the env var before running |
| Rate limit errors (429) | Wait a few minutes, or reduce `MAX_TURNS` |
| Agent not appearing on ASI:One | Make sure the mailbox connection is active and agent is running |
| No search results | Check that Tavily API key is valid and has remaining quota |
