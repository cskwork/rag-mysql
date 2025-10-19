# Claude Agent SDK Integration Guide

This document explains how to use the Claude Agent SDK as the SQL generation backend for the RAG MySQL project.

## Overview

Using `LLM_PROVIDER=claude` routes prompt generation through the Claude Agent SDK, enabling multi-turn interactions backed by Anthropic Claude models while keeping OpenAI embeddings for retrieval.

## Prerequisites

- An Anthropic API key with Claude access (`ANTHROPIC_API_KEY`).
- Python 3.10+ and Node.js (required by the Claude Agent SDK CLI).
- The `claude-agent-sdk` package (added in `requirements.txt`).
- An OpenAI API key (`OPENAI_API_KEY`) for embeddings.

## Configuration Steps

1. Set the provider in your `.env` file:
   ```bash
   LLM_PROVIDER=claude
   ```
2. Add the Anthropic credentials and Claude options:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-...
   CLAUDE_MODEL=claude-3-5-sonnet-latest
   CLAUDE_MAX_TURNS=6
   CLAUDE_SYSTEM_PROMPT="You are a helpful SQL assistant."
   ```
3. Keep `OPENAI_API_KEY` configured; the application still relies on OpenAI embeddings for ChromaDB.
4. Install dependencies and start the app as usual:
   ```bash
   pip install -r requirements.txt
   python app.py
   ```

## Multi-turn Behaviour

- The adapter maintains a rolling history (bounded by `CLAUDE_MAX_TURNS`) across requests, sending prior user and assistant turns alongside Vanna's few-shot context.
- To reset the conversation, restart the application or change the provider.

## Troubleshooting

- **Missing API key**: Ensure `ANTHROPIC_API_KEY` is present in the environment before launching the app.
- **Claude CLI errors**: The Agent SDK shell integration requires Node.js and the Claude Code CLI. Follow the official installation steps from [docs.claude.com](https://docs.claude.com/ko/api/agent-sdk/python).
- **Long conversations**: Increase `CLAUDE_MAX_TURNS` to retain more context, or lower it if you hit context limits.
