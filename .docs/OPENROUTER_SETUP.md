# OpenRouter Integration Setup Guide

This document explains how to use the newly integrated OpenRouter LLM provider in your RAG MySQL project.

## Overview

OpenRouter provides access to 200+ AI models through a single API, offering:
- ✅ Access to models from OpenAI, Anthropic, Meta, Google, and more
- ✅ Automatic fallbacks and cost optimization
- ✅ Unified pricing and billing
- ✅ OpenAI API compatibility

## Setup Instructions

### 1. Get OpenRouter API Key

1. Visit [https://openrouter.ai](https://openrouter.ai)
2. Create an account or sign in
3. Go to [Keys page](https://openrouter.ai/keys)
4. Create a new API key

### 2. Configure Environment Variables

Copy `env.example` to `.env` and configure:

```bash
# Set OpenRouter as your LLM provider
LLM_PROVIDER=openrouter

# OpenRouter configuration
OPENROUTER_API_KEY=sk-or-your-actual-api-key-here
OPENROUTER_MODEL=openai/gpt-4o
OPENROUTER_SITE_URL=http://localhost:8084
OPENROUTER_SITE_NAME=RAG-MySQL
```

### 3. Available Models

Popular models for SQL generation:
- `openai/gpt-4o` - Latest GPT-4 (recommended for best results)
- `openai/gpt-4` - GPT-4 standard
- `anthropic/claude-3.5-sonnet` - Excellent for code/SQL
- `meta-llama/llama-3.2-3b-instruct` - Fast and cost-effective
- `google/gemini-2.0-flash-exp` - Google's latest model

View all available models at: [https://openrouter.ai/models](https://openrouter.ai/models)

### 4. Usage

Run the application normally:

```bash
python app.py
```

You should see:
```
🌐 OpenRouter provider 사용 중 (model: openai/gpt-4o)
```

## Features

- **Multiple Model Access**: Switch between 200+ models by changing `OPENROUTER_MODEL`
- **Cost Optimization**: OpenRouter automatically selects the most cost-effective route
- **Fallback Support**: Automatic fallbacks if primary model is unavailable
- **Usage Attribution**: Track usage in OpenRouter dashboard with site attribution
- **Unified Billing**: One bill for all model providers

## Cost Benefits

OpenRouter often provides:
- Lower costs than direct provider APIs
- Volume discounts
- Shared rate limits across models
- No need for multiple API keys

## Troubleshooting

### Common Issues

1. **Invalid API Key Error**
   ```
   OpenRouter API key가 설정되지 않았습니다
   ```
   - Verify your API key is correct in `.env`
   - Ensure no extra spaces or quotes

2. **Model Not Found**
   - Check model name format: `provider/model-name`
   - Verify model exists at https://openrouter.ai/models

3. **Rate Limiting**
   - OpenRouter provides better rate limits than individual providers
   - Check your usage dashboard

### Model Selection Tips

For SQL generation tasks:
- **Best Quality**: `openai/gpt-4o`, `anthropic/claude-3.5-sonnet`
- **Balanced**: `openai/gpt-4`, `meta-llama/llama-3.1-8b-instruct`
- **Cost-Effective**: `meta-llama/llama-3.2-3b-instruct`

## Support

- OpenRouter Documentation: https://openrouter.ai/docs
- Model Information: https://openrouter.ai/models
- API Reference: https://openrouter.ai/docs/api-reference

## Migration from Other Providers

Switching from OpenAI or Ollama is simple:

1. Change `LLM_PROVIDER=openrouter` in your `.env`
2. Add OpenRouter configuration
3. Restart the application

Your existing training data and ChromaDB will be preserved.