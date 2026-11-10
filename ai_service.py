"""
AI Service layer providing integration and real-time token streaming with:
1. Demo / Local Mock Engine (instant offline streaming)
2. Google Gemini API (SSE streaming via streamGenerateContent)
3. OpenAI-compatible APIs (OpenAI, Ollama, Groq, OpenRouter via SSE stream: true)
"""

import asyncio
import json
import random
import re
import urllib.parse
from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx

IMAGE_PREFIX_PATTERNS = [
    r"^\s*/(?:image|imagine|draw|paint|img|generate-image)\b\s*",
    r"^\s*(?:can you |could you |please )?(?:generate|create|make|render|produce)\s+(?:an?|the)?\s*(?:ai\s+)?(?:image|picture|photo|illustration|drawing|artwork)\s+of\b\s*",
    r"^\s*(?:can you |could you |please )?(?:draw|paint)\s+(?:an?|the)?\s*(?:picture|image|illustration)\s+of\b\s*",
    r"^\s*(?:can you |could you |please )?(?:draw|paint)\s+(?:me\s+)?",
    r"^\s*(?:imagine|show me an image of|show me a picture of)\b\s*",
]


def is_image_request(text: str) -> bool:
    """Detects whether user prompt is asking to generate/draw an image."""
    if not text:
        return False
    t = text.strip()
    return any(re.search(pat, t, re.IGNORECASE) for pat in IMAGE_PREFIX_PATTERNS)


def extract_image_prompt(text: str) -> str:
    """Extracts the visual subject/description from an image generation request."""
    cleaned = text.strip()
    for pat in IMAGE_PREFIX_PATTERNS:
        match = re.search(pat, cleaned, re.IGNORECASE)
        if match:
            cleaned = cleaned[match.end():].strip()
            break
    cleaned = re.sub(r"[\.!\?]+$", "", cleaned).strip()
    return cleaned if cleaned else text.strip()


def get_flux_image_url(prompt: str, seed: Optional[int] = None, width: int = 1024, height: int = 1024) -> str:
    """Constructs high-definition FLUX.1 image generation URL from prompt."""
    seed_val = seed if seed is not None else random.randint(100000, 99999999)
    encoded = urllib.parse.quote(prompt.strip())
    return f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&seed={seed_val}&model=flux&nologo=true"


def format_image_markdown(prompt: str, image_url: str) -> str:
    """Formats markdown response containing rendered image and HD download link."""
    escaped_prompt = prompt.replace("\n", " ").strip()
    return (
        f"🎨 **Generated AI Image with FLUX.1**\n\n"
        f"**Prompt:** *\"{escaped_prompt}\"*\n\n"
        f"![{escaped_prompt}]({image_url})\n\n"
        f"[📥 **Click here to Open / Download Full HD Image**]({image_url})\n\n"
        f"> 💡 *Tip: You can generate different styles or variations anytime (e.g. \"/image {escaped_prompt} in anime style\" or \"photorealistic 8K render\")!*"
    )


class MockAIEngine:
    """Intelligent simulated AI assistant for immediate offline / keyless testing."""

    @staticmethod
    def generate_reply(messages: List[Dict[str, Any]], system_prompt: str) -> str:
        raw_last = messages[-1]["content"].strip() if messages else ""
        last_msg = raw_last.lower()

        # AI Image Generation requests
        if is_image_request(raw_last):
            prompt = extract_image_prompt(raw_last)
            url = get_flux_image_url(prompt)
            return format_image_markdown(prompt, url)

        # Coding requests
        if any(w in last_msg for w in ["python", "code", "function", "flutter", "flet", "react", "bug", "algorithm"]):
            return (
                "Here is an optimized, production-ready solution for your request:\n\n"
                "```python\n"
                "from typing import List, Dict, Any\n"
                "import time\n\n"
                "def process_data(items: List[int]) -> Dict[str, Any]:\n"
                "    \"\"\"Processes numbers and computes aggregate telemetry.\"\"\"\n"
                "    if not items:\n"
                "        return {\"count\": 0, \"total\": 0, \"avg\": 0.0, \"max\": None}\n\n"
                "    total = sum(items)\n"
                "    return {\n"
                "        \"count\": len(items),\n"
                "        \"total\": total,\n"
                "        \"avg\": round(total / len(items), 2),\n"
                "        \"max\": max(items),\n"
                "        \"min\": min(items),\n"
                "        \"processed_at\": time.strftime('%Y-%m-%d %H:%M:%S')\n"
                "    }\n\n"
                "# Example execution\n"
                "metrics = process_data([14, 28, 42, 59, 87, 102])\n"
                "for key, value in metrics.items():\n"
                "    print(f\"{key.capitalize()}: {value}\")\n"
                "```\n\n"
                "### Architectural Highlights:\n"
                "- **Type Hints:** Compliant with PEP 484 for static type checkers.\n"
                "- **Boundary Handling:** Robust fallback for empty list inputs.\n"
                "- **Performance:** Single pass $O(n)$ complexity with minimal memory allocations.\n\n"
                "Would you like me to add automated unit tests or adapt this for streaming pipelines?"
            )

        # Brainstorming / Planning
        if any(w in last_msg for w in ["idea", "brainstorm", "suggest", "recommend", "plan", "roadmap"]):
            return (
                "Here is a strategic design and architecture outline:\n\n"
                "### 1. Vision & Target User\n"
                "- **Core Goal:** Fast, fluid, cross-platform productivity across laptops and mobile devices.\n"
                "- **Key Metric:** Sub-50ms local UI response time and seamless offline capabilities.\n\n"
                "### 2. Implementation Roadmap\n"
                "1. **Phase 1: Foundation (Current)**\n"
                "   - Multi-session SQLite local database.\n"
                "   - Responsive Flutter/Flet UI with adaptive mobile drawers.\n"
                "   - Multi-engine AI provider abstraction.\n"
                "2. **Phase 2: Power Features**\n"
                "   - Real-time token streaming.\n"
                "   - Conversation export to Markdown and JSON.\n"
                "   - Global desktop keyboard shortcuts.\n"
                "3. **Phase 3: Extended Intelligence**\n"
                "   - Local file and code attachment parsing.\n"
                "   - Specialized persona prompt libraries.\n\n"
                "Which phase or feature would you like to prioritize next?"
            )

        # Creator / Developer inquiry
        if any(w in last_msg for w in ["who made", "who created", "who developed", "who built", "your creator", "developer", "who is keshav"]):
            return (
                "👋 **I am KESHAV AI, created and developed by Keshav Batra!**\n\n"
                "I am a versatile, cross-platform AI assistant designed to run seamlessly on iPhones, Android phones, laptops, and PCs."
            )

        # Greetings
        if any(w in last_msg for w in ["hi", "hello", "hey", "greetings", "good morning", "good evening"]):
            return (
                "👋 **Hello! Welcome to KESHAV AI.**\n\n"
                "I am your versatile assistant, optimized for both your laptop and mobile device.\n\n"
                "- 💻 **Code & Architecture:** Build scripts, review bugs, optimize queries.\n"
                "- 📝 **Drafting & Writing:** Compose clean emails, proposals, and summaries.\n"
                "- ⚙️ **Custom AI Providers:** Connect your **Google Gemini** or **OpenAI/Ollama** API keys in **Settings**.\n\n"
                "How can I assist your workflow today?"
            )

        # General inquiry
        return (
            f"Here is my analysis on: *\"{messages[-1]['content']}\"*\n\n"
            "### Core Analysis\n"
            "1. **Primary Insight:** Approaching this requires clean separation of concerns and clear data contracts.\n"
            "2. **Key Recommendation:** Validate your assumptions incrementally and ensure state updates remain idempotent.\n"
            "3. **Cross-Platform Compatibility:** Responsive layout rules ensure equal accessibility across laptop screens and mobile touch displays.\n\n"
            "> **Tip:** KESHAV AI is currently running in **Offline Demo Mode**. To enable live models, open **Settings** and add a Google Gemini or OpenAI/Ollama key."
        )


async def stream_demo_response(
    messages: List[Dict[str, Any]],
    system_prompt: str,
) -> AsyncGenerator[str, None]:
    """Streams demo reply token by token with realistic typing cadence."""
    reply = MockAIEngine.generate_reply(messages, system_prompt)
    words = reply.split(" ")

    accumulated = ""
    for i, word in enumerate(words):
        accumulated += (word + " " if i < len(words) - 1 else word)
        yield accumulated
        # Natural typing rhythm with micro-delays
        delay = 0.015 if len(word) > 4 else 0.008
        if word.endswith((".", "\n", ":")):
            delay = 0.04
        await asyncio.sleep(delay)


async def stream_gemini_api(
    messages: List[Dict[str, Any]],
    system_prompt: str,
    api_key: str,
    model: str = "gemini-3.5-flash-lite",
) -> AsyncGenerator[str, None]:
    """Streams responses from Google Gemini API via streamGenerateContent SSE with automatic high-demand failover."""
    if not api_key:
        raise ValueError("Google Gemini API key is missing. Please add it in Settings.")

    # Sanitize model name (remove legacy 'gemini-1.5' or 404 models)
    if not model or model.startswith("gemini-1.5") or model.startswith("gemini-2.5"):
        model = "gemini-3.5-flash-lite"

    # Multi-model resilience chain: if a model encounters a 503 high-demand spike, auto-switch
    models_to_try = [model]
    for fallback in ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.6-flash"]:
        if fallback not in models_to_try:
            models_to_try.append(fallback)

    contents = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    payload: Dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048,
        },
    }

    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    headers = {"Content-Type": "application/json"}
    accumulated = ""
    last_error = ""

    async with httpx.AsyncClient(timeout=60.0) as client:
        for idx, candidate_model in enumerate(models_to_try):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{candidate_model}:streamGenerateContent?alt=sse&key={api_key}"
            try:
                async with client.stream("POST", url, json=payload, headers=headers) as response:
                    if response.status_code in (503, 429):
                        # High demand spike on candidate model, attempt fallback
                        last_error = f"Gemini API model {candidate_model} is under high demand (503)."
                        if idx < len(models_to_try) - 1:
                            await asyncio.sleep(0.5)
                            continue
                        raise RuntimeError("Google's Gemini model is currently experiencing temporary high demand. Please try again in a few moments.")
                    elif response.status_code != 200:
                        err_text = await response.aread()
                        last_error = f"Gemini API Error ({response.status_code}): {err_text.decode('utf-8', errors='ignore')}"
                        if idx < len(models_to_try) - 1:
                            continue
                        raise RuntimeError(last_error)

                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data: "):
                            continue
                        json_str = line[6:].strip()
                        try:
                            data = json.loads(json_str)
                            candidates = data.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for part in parts:
                                    text_piece = part.get("text", "")
                                    if text_piece:
                                        accumulated += text_piece
                                        yield accumulated
                        except json.JSONDecodeError:
                            continue
                    return
            except httpx.RequestError as e:
                last_error = f"Network connection error: {e}"
                if idx < len(models_to_try) - 1:
                    continue
                raise RuntimeError(last_error)

    if not accumulated and last_error:
        raise RuntimeError(last_error)


async def stream_openai_api(
    messages: List[Dict[str, Any]],
    system_prompt: str,
    api_key: str,
    base_url: str = "https://api.openai.com/v1",
    model: str = "gpt-4o",
) -> AsyncGenerator[str, None]:
    """Streams responses from OpenAI-compatible API or free ChatGPT gateway."""
    # Fast path: If no custom key is provided, use free fast ChatGPT gateway
    if not api_key:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://text.pollinations.ai/",
                json={
                    "messages": [{"role": "system", "content": system_prompt}] + [
                        {"role": m["role"], "content": m["content"]} for m in messages
                    ],
                    "model": "openai-fast",
                },
            )
            if resp.status_code == 200:
                text = resp.text.strip()
                words = text.split(" ")
                accumulated = ""
                for i, w in enumerate(words):
                    accumulated += (w + " " if i < len(words) - 1 else w)
                    yield accumulated
                    await asyncio.sleep(0.015)
                return
            else:
                raise RuntimeError(f"ChatGPT free gateway returned {resp.status_code}")

    clean_base = base_url.rstrip("/")
    if not clean_base.endswith("/v1") and "ollama" not in clean_base and "groq" not in clean_base:
        url = f"{clean_base}/v1/chat/completions"
    else:
        url = f"{clean_base}/chat/completions"

    formatted_messages = []
    if system_prompt:
        formatted_messages.append({"role": "system", "content": system_prompt})

    for msg in messages:
        formatted_messages.append({
            "role": "user" if msg["role"] == "user" else "assistant",
            "content": msg["content"],
        })

    payload = {
        "model": model,
        "messages": formatted_messages,
        "temperature": 0.7,
        "stream": True,
    }

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    accumulated = ""

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as response:
            if response.status_code != 200:
                err_text = await response.aread()
                raise RuntimeError(f"OpenAI API Error ({response.status_code}): {err_text.decode('utf-8', errors='ignore')}")

            async for line in response.aiter_lines():
                line = line.strip()
                if not line or not line.startswith("data: "):
                    continue
                if line == "data: [DONE]":
                    break
                json_str = line[6:].strip()
                try:
                    data = json.loads(json_str)
                    choices = data.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content_piece = delta.get("content", "")
                        if content_piece:
                            accumulated += content_piece
                            yield accumulated
                except json.JSONDecodeError:
                    continue


async def stream_claude_api(
    messages: List[Dict[str, Any]],
    system_prompt: str,
    api_key: str,
    model: str = "claude-3-5-sonnet-20241022",
) -> AsyncGenerator[str, None]:
    """Streams responses from Anthropic Claude API via SSE."""
    if not api_key:
        raise ValueError(
            "Anthropic Claude API key is missing.\n\n"
            "Please paste your Anthropic key (`sk-ant-...`) in this chat box or in ⚙️ Settings."
        )

    url = "https://api.anthropic.com/v1/messages"

    formatted_messages = []
    for msg in messages:
        formatted_messages.append({
            "role": "user" if msg["role"] == "user" else "assistant",
            "content": msg["content"],
        })

    payload: Dict[str, Any] = {
        "model": model,
        "max_tokens": 2048,
        "messages": formatted_messages,
        "stream": True,
    }
    if system_prompt:
        payload["system"] = system_prompt

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    accumulated = ""
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as response:
            if response.status_code != 200:
                err_text = await response.aread()
                raise RuntimeError(f"Claude API Error ({response.status_code}): {err_text.decode('utf-8', errors='ignore')}")

            async for line in response.aiter_lines():
                line = line.strip()
                if not line or not line.startswith("data: "):
                    continue
                json_str = line[6:].strip()
                try:
                    data = json.loads(json_str)
                    event_type = data.get("type", "")
                    if event_type == "content_block_delta":
                        text_piece = data.get("delta", {}).get("text", "")
                        if text_piece:
                            accumulated += text_piece
                            yield accumulated
                except json.JSONDecodeError:
                    continue


async def stream_ai_response(
    messages: List[Dict[str, Any]],
    settings: Dict[str, str],
) -> AsyncGenerator[str, None]:
    """Unified entrypoint for streaming AI responses based on selected provider."""
    # Fast path for AI Image Generation requests across all providers
    raw_last = messages[-1]["content"].strip() if messages else ""
    if is_image_request(raw_last):
        prompt = extract_image_prompt(raw_last)
        url = get_flux_image_url(prompt)
        yield format_image_markdown(prompt, url)
        return

    provider = settings.get("provider", "gemini").lower()
    system_prompt = settings.get("system_prompt", "")

    if provider == "gemini":
        api_key = settings.get("gemini_api_key", "").strip()
        model = settings.get("gemini_model", "gemini-3.5-flash-lite")
        async for chunk in stream_gemini_api(messages, system_prompt, api_key, model):
            yield chunk

    elif provider in ("openai", "chatgpt"):
        api_key = settings.get("openai_api_key", "").strip()
        base_url = settings.get("openai_base_url", "https://api.openai.com/v1").strip()
        model = settings.get("openai_model", "gpt-4o")
        async for chunk in stream_openai_api(messages, system_prompt, api_key, base_url, model):
            yield chunk

    elif provider in ("claude", "anthropic"):
        api_key = settings.get("claude_api_key", "").strip()
        model = settings.get("claude_model", "claude-3-5-sonnet-20241022")
        async for chunk in stream_claude_api(messages, system_prompt, api_key, model):
            yield chunk

    else:
        async for chunk in stream_demo_response(messages, system_prompt):
            yield chunk


async def get_ai_response(
    messages: List[Dict[str, Any]],
    settings: Dict[str, str],
) -> str:
    """Non-streaming fallback."""
    last_chunk = ""
    async for chunk in stream_ai_response(messages, settings):
        last_chunk = chunk
    return last_chunk
