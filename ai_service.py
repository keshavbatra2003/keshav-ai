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

VIDEO_PREFIX_PATTERNS = [
    r"^\s*/(?:video|animate|animation|make-video|generate-video|create-video)\b\s*",
    r"^\s*(?:can you |could you |please )?(?:generate|create|make|produce|render)\s+(?:an?|the)?\s*(?:ai\s+)?(?:video|animation|clip|motion|short|reel)\s+(?:of|about|on)?\b\s*",
    r"^\s*(?:make|create)\s+a\s+video\s+(?:of|about|on)?\b\s*",
]

SEARCH_PREFIX_PATTERNS = [
    r"^\s*/(?:search|web|browse|google|ddg|lookup)\b\s*",
    r"^\s*(?:can you |could you |please )?(?:search|browse|lookup|check)(?:\s+(?:the|for|on))?\s+web\s+(?:for|about)?\b\s*",
    r"^\s*(?:what is the latest|latest news|current news|breaking news)\s+(?:on|about)?\b\s*",
    r"^\s*(?:who won|current price of|today's news on)\b\s*",
]


def is_search_request(text: str) -> bool:
    """Detects whether user prompt requests a live real-time web search."""
    if not text:
        return False
    t = text.strip()
    return any(re.search(pat, t, re.IGNORECASE) for pat in SEARCH_PREFIX_PATTERNS)


def extract_search_query(text: str) -> str:
    """Extracts search query keywords from a search command or natural inquiry."""
    cleaned = text.strip()
    for pat in SEARCH_PREFIX_PATTERNS:
        match = re.search(pat, cleaned, re.IGNORECASE)
        if match:
            cleaned = cleaned[match.end():].strip()
            break
    cleaned = re.sub(r"[\.!\?]+$", "", cleaned).strip()
    return cleaned if cleaned else text.strip()


async def search_duckduckgo(query: str) -> Optional[str]:
    """Queries DuckDuckGo Instant Answer API for live encyclopedic and web context."""
    if not query:
        return None
    encoded = urllib.parse.quote(query.strip())
    url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (KESHAV-AI-Bot)"})
            if resp.status_code != 200:
                return None
            data = resp.json()
            abstract = data.get("AbstractText", "").strip()
            source = data.get("AbstractSource", "")
            src_url = data.get("AbstractURL", "")
            heading = data.get("Heading", "")

            topics = []
            for t in data.get("RelatedTopics", []):
                if isinstance(t, dict) and "Text" in t:
                    topics.append(t["Text"])
                    if len(topics) >= 4:
                        break

            if not abstract and not topics:
                return None

            res = []
            if heading or abstract:
                res.append(f"**{heading}**\n{abstract}" if heading else abstract)
                if src_url:
                    res.append(f"*Source: [{source if source else 'Web'}]({src_url})*")
            if topics:
                res.append("**Related Live Context:**\n" + "\n".join(f"- {item}" for item in topics))
            return "\n\n".join(res)
    except Exception as e:
        print(f"Web search error: {e}")
        return None


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


def is_video_request(text: str) -> bool:
    """Detects whether user prompt is asking to generate/create a video or animation."""
    if not text:
        return False
    t = text.strip()
    return any(re.search(pat, t, re.IGNORECASE) for pat in VIDEO_PREFIX_PATTERNS)


def extract_video_prompt(text: str) -> str:
    """Extracts the cinematic video concept from a video generation request."""
    cleaned = text.strip()
    for pat in VIDEO_PREFIX_PATTERNS:
        match = re.search(pat, cleaned, re.IGNORECASE)
        if match:
            cleaned = cleaned[match.end():].strip()
            break
    cleaned = re.sub(r"[\.!\?]+$", "", cleaned).strip()
    return cleaned if cleaned else text.strip()


def format_video_production(prompt: str, keyframe_url: str) -> str:
    """Formats a complete Hollywood-grade AI video production storyboard and prompts."""
    escaped_prompt = prompt.replace("\n", " ").strip()
    luma_url = "https://lumalabs.ai/dream-machine"
    runway_url = "https://runwayml.com/"
    kling_url = "https://klingai.com/"

    return (
        f"🎬 **KESHAV AI Video Creation Studio**\n\n"
        f"**Concept:** *\"{escaped_prompt}\"*\n\n"
        f"### 🖼️ Cinematic 16:9 Keyframe Preview:\n"
        f"![{escaped_prompt}]({keyframe_url})\n\n"
        f"[📥 **Click to Open / Download Full 16:9 4K Film Still**]({keyframe_url})\n\n"
        f"---\n\n"
        f"### 🎥 Scene-by-Scene Director's Storyboard:\n\n"
        f"**Scene 1: Opening Shot (00:00 - 00:05)**\n"
        f"- 📷 **Camera:** Wide cinematic drone pan, establishing depth and scale.\n"
        f"- 💡 **Lighting & Atmosphere:** 35mm anamorphic lens, volumetric light rays, 4K HDR color tone.\n"
        f"- 🎵 **Sound & Score:** Ambient rising synth tone with deep atmospheric reverb.\n\n"
        f"**Scene 2: Core Action & Motion (00:05 - 00:15)**\n"
        f"- 📷 **Camera:** Dynamic tracking orbit shot following: *\"{escaped_prompt}\"*.\n"
        f"- ⚡ **Motion Dynamics:** Fluid high-speed motion, realistic wind and particle physics.\n"
        f"- 🎙️ **Voiceover Narration:** *\"Every innovation begins as a vision in motion.\"*\n\n"
        f"**Scene 3: Climax & Reveal (00:15 - 00:30)**\n"
        f"- 📷 **Camera:** Slow-motion dolly zoom with dramatic lighting bloom.\n"
        f"- 🎵 **Sound & Score:** Inspiring bass drop resolving into a powerful cinematic crescendo.\n\n"
        f"---\n\n"
        f"### 🚀 Ready-to-Render Video Engine Prompt:\n\n"
        f"```text\n"
        f"Cinematic 4K hyperrealistic footage of {escaped_prompt}, smooth tracking camera movement, 35mm lens, photorealistic textures, dynamic atmospheric lighting, 60fps ultra smooth motion, masterpiece\n"
        f"```\n\n"
        f"**Render with Top Free Video Engines:**\n"
        f"- 🔗 [Render on **Luma Dream Machine** (Free Tier)]({luma_url})\n"
        f"- 🔗 [Render on **Kling AI** (Free Daily Credits)]({kling_url})\n"
        f"- 🔗 [Render on **Runway Gen-3**]({runway_url})\n\n"
        f"> 💡 *Tip: Copy the prompt above and paste it directly into Luma or Kling to render the live motion MP4 clip for free!*"
    )


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

        # AI Video Creation requests
        if is_video_request(raw_last):
            prompt = extract_video_prompt(raw_last)
            url = get_flux_image_url(f"cinematic 16:9 movie still of {prompt}, 4k photorealistic film footage", width=1280, height=720)
            return format_video_production(prompt, url)

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

        # Casual reactions & positive feedback
        if last_msg in ["wow", "cool", "great", "nice", "awesome", "super", "perfect", "good", "thanks", "thank you", "ty", "yay"]:
            return (
                "Thank you! 😊 I'm glad I could help. What should we tackle next?\n\n"
                "- 💻 **Code:** Write or debug a script in Python, JS, or SQL\n"
                "- 🎨 **Image:** Generate high-definition art with `/image <prompt>`\n"
                "- 🌐 **Search:** Search the live web with `/search <query>`\n"
                "- 📄 **Documents:** Attach a PDF or code file with the `+` button to summarize it!"
            )

        # Greetings
        if any(w in last_msg for w in ["hi", "hello", "hey", "yo", "sup", "greetings", "good morning", "good evening"]):
            return (
                "👋 **Hello! Welcome to KESHAV AI.**\n\n"
                "I am your smart assistant created by Keshav Batra, optimized for both your laptop and mobile device.\n\n"
                "- 💻 **Code & Architecture:** Build scripts, review bugs, optimize queries.\n"
                "- 🎨 **Image Generation:** Create high-definition art via `/image <description>`.\n"
                "- 🌐 **Live Web Search:** Find current news & facts via `/search <query>`.\n"
                "- 📄 **Document Analysis:** Attach any PDF or text file with `+` for instant answers.\n\n"
                "How can I assist your workflow today?"
            )

        # General inquiry
        return (
            f"Here is my analysis on: *\"{raw_last}\"*\n\n"
            "### Key Insights & Observations:\n"
            "1. **Primary Focus:** Addressing this effectively requires clear structure, modular components, and verifying edge cases.\n"
            "2. **Strategic Approach:** Breaking the challenge into smaller, measurable steps yields the cleanest results.\n"
            "3. **Practical Next Step:** Validate the foundational contract first, then iterate toward optimal performance.\n\n"
            "Would you like me to dive deeper into any specific aspect or explore code implementations for this?"
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
    model: str = "gemini-2.0-flash-lite",
) -> AsyncGenerator[str, None]:
    """Streams responses from Google Gemini API via streamGenerateContent SSE with automatic high-demand failover."""
    if not api_key:
        raise ValueError("Google Gemini API key is missing. Please add it in Settings.")

    # Sanitize model name — map legacy/fictional names to real Google models
    legacy_map = {
        "gemini-3.5-flash-lite": "gemini-2.0-flash-lite",
        "gemini-3.5-flash": "gemini-2.0-flash",
        "gemini-3.6-flash": "gemini-2.0-flash",
        "gemini-3.1-pro-preview": "gemini-2.5-pro-preview-05-06",
        "gemini-flash-latest": "gemini-2.0-flash",
    }
    if not model:
        model = "gemini-2.0-flash-lite"
    elif model in legacy_map:
        model = legacy_map[model]
    elif model.startswith("gemini-1.5"):
        model = "gemini-2.0-flash"

    # Multi-model resilience chain: if a model encounters a 503 high-demand spike, auto-switch
    models_to_try = [model]
    for fallback in ["gemini-2.0-flash-lite", "gemini-2.0-flash", "gemini-1.5-flash"]:
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
                        raise RuntimeError("Google's Gemini API is temporarily unavailable due to high demand. Please try again in a few moments, or switch to ChatGPT in the model switcher.")
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
    # Fast path: If no custom key is provided, use free fast ChatGPT gateway with resilience
    if not api_key:
        browser_headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/plain, */*",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            for candidate in ["openai-fast", "openai"]:
                try:
                    resp = await client.post(
                        "https://text.pollinations.ai/",
                        json={
                            "messages": [{"role": "system", "content": system_prompt}] + [
                                {"role": m["role"], "content": m["content"]} for m in messages
                            ],
                            "model": candidate,
                        },
                        headers=browser_headers,
                    )
                    if resp.status_code == 200 and resp.text.strip():
                        text = resp.text.strip()
                        words = text.split(" ")
                        accumulated = ""
                        for i, w in enumerate(words):
                            accumulated += (w + " " if i < len(words) - 1 else w)
                            yield accumulated
                            await asyncio.sleep(0.015)
                        return
                except Exception:
                    continue

        raise RuntimeError("ChatGPT free gateway temporarily busy")

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


async def stream_ai_response(
    messages: List[Dict[str, Any]],
    settings: Dict[str, str],
) -> AsyncGenerator[str, None]:
    """Unified entrypoint for streaming AI responses based on selected provider."""
    # Fast path for AI Video Creation requests across all providers
    raw_last = messages[-1]["content"].strip() if messages else ""
    if is_video_request(raw_last):
        prompt = extract_video_prompt(raw_last)
        url = get_flux_image_url(f"cinematic 16:9 movie still of {prompt}, 4k photorealistic film footage", width=1280, height=720)
        yield format_video_production(prompt, url)
        return

    # Fast path for AI Image Generation requests across all providers
    if is_image_request(raw_last):
        prompt = extract_image_prompt(raw_last)
        url = get_flux_image_url(prompt)
        yield format_image_markdown(prompt, url)
        return

    provider = settings.get("provider", "gemini").lower()
    system_prompt = settings.get("system_prompt", "")

    # Live Real-Time Web Search Augmentation
    if messages and is_search_request(raw_last):
        search_query = extract_search_query(raw_last)
        web_info = await search_duckduckgo(search_query)
        if web_info:
            web_context = (
                f"\n\n[REAL-TIME LIVE WEB SEARCH RESULTS FOR '{search_query}']:\n"
                f"{web_info}\n\n"
                f"[Instructions: Use the real-time web context above to provide an accurate, up-to-date answer. "
                f"Begin your reply with '🌐 **Live Web Search**' and cite sources if available.]"
            )
            system_prompt = (system_prompt + web_context) if system_prompt else web_context

    if provider == "gemini":
        api_key = settings.get("gemini_api_key", "").strip()
        model = settings.get("gemini_model", "gemini-2.0-flash-lite")
        try:
            async for chunk in stream_gemini_api(messages, system_prompt, api_key, model):
                yield chunk
        except Exception:
            # Fallback to ChatGPT free gateway or built-in engine
            try:
                async for chunk in stream_openai_api(messages, system_prompt, "", model="gpt-4o"):
                    yield chunk
            except Exception:
                async for chunk in stream_demo_response(messages, system_prompt):
                    yield chunk

    elif provider in ("openai", "chatgpt"):
        api_key = settings.get("openai_api_key", "").strip()
        base_url = settings.get("openai_base_url", "https://api.openai.com/v1").strip()
        model = settings.get("openai_model", "gpt-4o")
        try:
            async for chunk in stream_openai_api(messages, system_prompt, api_key, base_url, model):
                yield chunk
        except Exception:
            # Automatic failover to Gemini if configured, else built-in engine
            gemini_key = settings.get("gemini_api_key", "").strip()
            if gemini_key:
                try:
                    async for chunk in stream_gemini_api(messages, system_prompt, gemini_key, "gemini-2.0-flash-lite"):
                        yield chunk
                    return
                except Exception:
                    pass
            async for chunk in stream_demo_response(messages, system_prompt):
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
