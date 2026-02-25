# Backend API Documentation

## `/api/generate-website` - LangGraph Multi-Page Website Generator

### Overview
This endpoint generates complete multi-page websites using a sophisticated **LangGraph workflow** powered by conversational AI. The system intelligently gathers business requirements through interactive dialogue, automatically detects and scrapes reference URLs for design inspiration, plans website structure, generates custom images with DALL-E 3, and creates production-ready multi-page HTML/CSS websites.

### Key Features
- 🤖 **Intelligent Business Gathering**: Progressive conversation with context-aware counter-questions
- 🌐 **Reference URL Detection**: Automatically scrapes and analyzes reference websites for design patterns
- 📊 **6-Stage Workflow**: Business Gathering → Planning → Image Description → Image Generation → HTML Generation → File Storage
- 🔄 **Real-Time Streaming**: Server-Sent Events (SSE) with progress updates for each stage
- 💬 **Thread Continuity**: Stateful conversation memory across multiple requests
- 📄 **Multi-Page Support**: Generates complete websites with navigation, sections, and responsive design
- 🎨 **Smart Design System**: Automatically applies extracted design patterns from reference sites

---

## Endpoint Details

**Method:** `POST`  
**URL:** `/api/generate-website`  
**Content-Type:** `application/json`  
**Response Type:** `text/event-stream` (Server-Sent Events)

---

## Request Format

### Request Body Schema

```json
{
  "description": "string (required, min 10 chars)",
  "thread_id": "string (optional)",
  "messages": [
    {
      "role": "string (human|ai|system)",
      "content": "string"
    }
  ]
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | ✅ Yes | Business description, requirements, or user message (minimum 10 characters). Can include reference URLs. |
| `thread_id` | string | ❌ No | Thread ID for conversation continuity (returned from previous request). Required for follow-up conversations. |
| `messages` | array | ❌ No | Complete conversation history with all previous messages. Required for multi-turn conversations. |

### Message Object Schema

Each message in the `messages` array follows this structure:

```json
{
  "role": "human | ai | system",
  "content": "Message content as string"
}
```

**Role Types:**
- `human`: User messages (questions, answers, requirements)
- `ai`: Assistant responses (questions, clarifications, summaries)
- `system`: System prompts and instructions (internal use)

---

## Complete Workflow Stages

The LangGraph workflow executes through **6 sequential nodes**, each handling a specific aspect of website generation:

### Stage Flow Diagram

```
START 
  ↓
[1] BUSINESS GATHERING (0-10%)
  ↓ (ready=false) ───→ Return questions → Wait for user input
  ↓ (ready=true)
[2] PLANNING (10-25%)
  ↓
[3] IMAGE DESCRIPTION (25-40%)
  ↓
[4] IMAGE GENERATION (40-65%)
  ↓
[5] HTML GENERATION (65-90%)
  ↓
[6] FILE STORAGE (90-100%)
  ↓
END (status=completed)
```

---

### 📋 Stage 1: Business Gathering (0-10%)

**Purpose:** Progressively gather and validate business requirements through intelligent conversation.

**Node:** `business_gathering_node`

**Responsibilities:**
1. Analyze user input and conversation history
2. Detect and scrape reference URLs (if provided)
3. Build progressive business plan based on current information
4. Determine if sufficient information is available OR ask clarifying questions
5. Handle multi-turn conversations with context retention

**Special Features:**
- **Reference URL Detection**: Automatically detects URLs in user input (e.g., "I want a site like https://example.com")
- **Web Scraping Integration**: Scrapes reference sites for design patterns (colors, fonts, structure, layout)
- **Progressive Planning**: Generates draft → refined → finalized business plans across iterations
- **Smart Stopping**: Recognizes user phrases like "ready to generate", "go ahead", "you decide"

**State Updates:**
- `ready`: `false` (needs more info) or `true` (ready to proceed)
- `business_plan`: Progressive draft of business understanding
- `clarification_questions`: Array of questions to ask user (if ready=false)
- `reference_url`: Detected reference URL from user input
- `reference_analysis`: Scraped design data from reference site
- `messages`: Updated conversation history

**Response When Awaiting Input:**
```json
{
  "step": "business_gathering",
  "status": "awaiting_input",
  "progress": 5,
  "ready": false,
  "questions": [
    "What specific pages or sections do you need? (e.g., home, about, services, contact)",
    "Who is your target audience?",
    "What is the main goal of this website?"
  ],
  "thread_id": "1707912345",
  "message": "Please provide more information",
  "messages": [...]
}
```

**Response When Ready:**
```json
{
  "step": "business_gathering",
  "status": "in_progress",
  "progress": 10,
  "ready": true,
  "message": "✓ Business information gathered, proceeding to planning"
}
```

---

### 🎯 Stage 2: Planning (10-25%)

**Purpose:** Generate comprehensive website structure, styling strategy, and page architecture.

**Node:** `planning_node`

**Responsibilities:**
1. Analyze business requirements from gathering phase
2. Inject reference site design patterns (if available)
3. Generate website plan with pages, sections, navigation, and styling
4. Define color schemes, fonts, and design themes
5. Determine image requirements (hero, features, testimonials)

**Inputs:**
- `business_plan`: Validated business requirements
- `reference_analysis`: Design insights from scraped reference site (optional)
- `description`: Original user description

**State Updates:**
- `plan`: Complete website plan (JSON object)
- `plan_json`: Stringified JSON of the plan
- `template_styling`: Extracted styling patterns from reference (optional)
- `css_theme`: Global CSS theme definition (optional)

**Plan Structure:**
```json
{
  "pages": [
    {
      "name": "home",
      "purpose": "Landing page with hero and CTA",
      "sections": ["hero", "features", "testimonials", "cta"]
    },
    {
      "name": "about",
      "purpose": "Company story and team",
      "sections": ["story", "team", "values"]
    },
    {
      "name": "contact",
      "purpose": "Contact form and information",
      "sections": ["form", "info", "map"]
    }
  ],
  "styling": {
    "theme": "modern",
    "primary_color": "#3B82F6",
    "secondary_color": "#64748B",
    "font_family": "Inter, sans-serif",
    "design_style": "clean, professional, trustworthy"
  },
  "image_sections": ["hero", "features", "testimonials"],
  "navigation": ["home", "about", "services", "contact"]
}
```

**Response:**
```json
{
  "step": "planning",
  "status": "in_progress",
  "progress": 25,
  "message": "✓ Planning complete: 3 pages planned"
}
```

---

### 🖼️ Stage 3: Image Description (25-40%)

**Purpose:** Generate AI-optimized image prompts for DALL-E 3 based on website plan and business context.

**Node:** `image_description_node`

**Responsibilities:**
1. Identify sections requiring images (hero, features, testimonials)
2. Generate contextual DALL-E prompts for each image
3. Parallel execution for speed (async tasks)
4. Fallback descriptions if generation fails

**Parallel Execution:**
- Uses `asyncio.to_thread()` and `asyncio.gather()` for concurrent generation
- Significantly reduces total processing time

**Image Sections:**
- `hero`: Main landing page hero image
- `features`: Feature/benefits section image
- `testimonials`: Social proof/testimonials section image

**State Updates:**
- `image_descriptions`: Dictionary of section → description mappings

**Example Descriptions:**
```json
{
  "hero": "Modern coffee shop interior with warm lighting, customers enjoying coffee, cozy atmosphere, natural wood furniture, plants, professional photography style",
  "features": "Flat lay of organic coffee beans, fair trade certification badge, eco-friendly packaging, minimalist, clean background",
  "testimonials": "Happy diverse customers in coffee shop, smiling, holding coffee cups, candid authentic moment, natural lighting"
}
```

**Response:**
```json
{
  "step": "image_description",
  "status": "in_progress",
  "progress": 40,
  "message": "✓ Image descriptions ready for 3 sections"
}
```

---

### 🎨 Stage 4: Image Generation (40-65%)

**Purpose:** Generate high-quality images using DALL-E 3 with automatic fallback to static images.

**Node:** `image_generation_node`

**Responsibilities:**
1. Call Azure OpenAI DALL-E 3 API for each image
2. Download and save generated images locally
3. Parallel execution for speed
4. Automatic fallback to static placeholder images on failure
5. Generate public URLs for all images

**Configuration:**
- **Size**: 1792x1024 (landscape, high resolution)
- **Quality**: Standard
- **Parallel Execution**: All images generated concurrently

**Fallback Strategy:**
- If DALL-E API fails, uses pre-generated static images
- Ensures workflow never fails due to image generation issues

**State Updates:**
- `image_urls`: Dictionary of section → URL mappings

**Example URLs:**
```json
{
  "hero": "http://127.0.0.1:8000/uploads/hero_1707912345.png",
  "features": "http://127.0.0.1:8000/uploads/features_1707912346.png",
  "testimonials": "http://127.0.0.1:8000/uploads/testimonials_1707912347.png"
}
```

**Response:**
```json
{
  "step": "image_generation",
  "status": "in_progress",
  "progress": 65,
  "message": "✓ 3 images generated successfully"
}
```

---

### 💻 Stage 5: HTML Generation (65-90%)

**Purpose:** Generate production-ready multi-page HTML/CSS with responsive design and proper navigation.

**Node:** `html_generation_node`

**Responsibilities:**
1. Detect single-page vs multi-page website architecture
2. Generate complete HTML for each page with proper DOCTYPE and structure
3. Create appropriate navigation (anchor links for single-page, page links for multi-page)
4. Inject generated images into HTML
5. Extract inline CSS from `<style>` tags
6. Validate HTML structure and completeness
7. Ensure responsive design and mobile compatibility

**Navigation Strategy:**

**Single-Page Websites:**
- Navigation uses anchor links (`href="#section-name"`)
- All sections on one page with scroll behavior
- Example: `<a href="#hero">`, `<a href="#features">`

**Multi-Page Websites:**
- Navigation uses page links (`href="page-name.html"`)
- Separate HTML files for each page
- Example: `<a href="home.html">`, `<a href="about.html">`

**Validation:**
- Ensures HTML starts with `<!DOCTYPE` or `<html>`
- Verifies minimum length (100+ characters)
- Checks for closing `</html>` tag
- Validates section IDs for single-page sites

**State Updates:**
- `pages`: Dictionary of page_name → {html: string, css: string}

**Example Pages Output:**
```json
{
  "home": {
    "html": "<!DOCTYPE html><html>...</html>",
    "css": "/* Global styles */"
  },
  "about": {
    "html": "<!DOCTYPE html><html>...</html>",
    "css": ""
  },
  "contact": {
    "html": "<!DOCTYPE html><html>...</html>",
    "css": ""
  }
}
```

**Response:**
```json
{
  "step": "html_generation",
  "status": "in_progress",
  "progress": 90,
  "message": "✓ HTML generated for 3 pages, preparing to save files..."
}
```

---

### 💾 Stage 6: File Storage (90-100%)

**Purpose:** Save complete website to structured folder with proper file organization.

**Node:** `file_storage_node`

**Responsibilities:**
1. Create timestamped website folder
2. Extract CSS from HTML into separate `style.css` file
3. Replace inline `<style>` tags with `<link>` to external stylesheet
4. Save all HTML pages as separate files
5. Create `data.json` with metadata
6. Generate folder structure and file paths

**Folder Structure:**
```
webtemplates/
  └── website_20260216_141000/
      ├── index.html
      ├── about.html
      ├── contact.html
      ├── style.css
      └── data.json
```

**State Updates:**
- `folder_path`: Full path to website folder
- `saved_files`: Dictionary of filename → file_path mappings

**Response:**
```json
{
  "step": "file_storage",
  "status": "completed",
  "progress": 100,
  "message": "✓ Website generation complete: 3 pages saved to website_20260216_141000"
}
```

---

## Response Scenarios

### Scenario 1: Counter-Questions Flow (Insufficient Information)

**Initial Request:**
```json
POST /api/generate-website
{
  "description": "I want a website for my coffee shop"
}
```

**Response Stream:**
```
data: {"step":"business_gathering","status":"awaiting_input","progress":5,"ready":false,"questions":["What's the name of your coffee shop?","What makes your coffee shop unique?","Do you offer online ordering?"],"thread_id":"1707912345","message":"Please provide more information","messages":[{"role":"human","content":"I want a website for my coffee shop"},{"role":"ai","content":"I need more information:\n- What's the name of your coffee shop?\n- What makes your coffee shop unique?\n- Do you offer online ordering?"}]}

```

**Follow-Up Request:**
```json
POST /api/generate-website
{
  "description": "Name: Bean Haven. Organic fair-trade coffee. Yes, online ordering. Open 7am-8pm daily.",
  "thread_id": "1707912345",
  "messages": [
    {"role": "human", "content": "I want a website for my coffee shop"},
    {"role": "ai", "content": "I need more information:\n- What's the name..."},
    {"role": "human", "content": "Name: Bean Haven. Organic fair-trade coffee..."}
  ]
}
```

**Response Stream:**
```
data: {"step":"planning","status":"in_progress","progress":10,...}
data: {"step":"planning","status":"in_progress","progress":25,...}
data: {"step":"image_description","status":"in_progress","progress":40,...}
data: {"step":"image_generation","status":"in_progress","progress":65,...}
data: {"step":"html_generation","status":"in_progress","progress":90,...}
data: {"step":"file_storage","status":"completed","progress":100,"ready":true,"thread_id":"1707912345","message":"✓ Website generation complete","data":{...}}

```

---

### Scenario 2: Direct Generation (Comprehensive Description)

**Request:**
```json
POST /api/generate-website
{
  "description": "Professional portfolio for Sarah Chen, UX/UI designer. Pages: Home (hero, featured work, CTA), About (bio, skills, process), Portfolio (10 case studies with filters), Contact (form, social). Color: purple & white, minimalist modern design, target audience: tech startups."
}
```

**Response Stream:**
```
data: {"step":"planning","status":"in_progress","progress":10,...}
data: {"step":"planning","status":"in_progress","progress":25,...}
data: {"step":"image_description","status":"in_progress","progress":40,...}
data: {"step":"image_generation","status":"in_progress","progress":65,...}
data: {"step":"html_generation","status":"in_progress","progress":90,...}
data: {"step":"complete","status":"completed","progress":100,...}

```

---

### Scenario 3: Reference URL Scraping

**Request:**
```json
POST /api/generate-website
{
  "description": "Create a website for my bakery, similar to https://example-bakery.com"
}
```

**Response Stream:**
```
data: {"step":"business_gathering","status":"in_progress","progress":5,"message":"🔍 Reference URL detected, analyzing design patterns..."}
data: {"step":"business_gathering","status":"awaiting_input","progress":5,"ready":false,"questions":["What's your bakery's name?","What products do you specialize in?"],"thread_id":"1707912345","messages":[...,{"role":"ai","content":"[REFERENCE SITE ANALYSIS]\nI've analyzed https://example-bakery.com\n\nDesign Insights:\n- Color Palette: Warm earth tones (#D4A574, #8B4513)\n- Typography: Playfair Display (headings), Open Sans (body)\n- Layout: Grid-based with full-width hero\n- Navigation: Fixed header with logo left, menu right\n\nI'll use these patterns as inspiration."}]}

```

---

### Scenario 4: Error During Workflow

**Request:**
```json
POST /api/generate-website
{
  "description": "xyz"
}
```

**Response:**
```
HTTP 400 Bad Request
{
  "detail": "Description must be at least 10 characters long"
}
```

**Or during workflow:**
```
data: {"step":"planning","status":"in_progress","progress":10,...}
data: {"step":"failed","status":"failed","progress":10,"message":"Error: Planning failed: Invalid JSON","error":"Planning failed: Invalid JSON"}

```

---

## Complete Response Schema

### Successful Completion Response

```json
{
  "step": "complete",
  "status": "completed",
  "progress": 100,
  "ready": true,
  "thread_id": "1707912345",
  "message": "✓ Website generation complete",
  "data": {
    "pages": {
      "home": {
        "html": "<!DOCTYPE html>...",
        "css": "* { margin: 0; padding: 0; }..."
      },
      "about": {
        "html": "<!DOCTYPE html>...",
        "css": ""
      }
    },
    "image_urls": {
      "hero": "http://127.0.0.1:8000/uploads/hero_1707912345.png",
      "features": "http://127.0.0.1:8000/uploads/features_1707912346.png"
    },
    "plan": {
      "pages": [
        {
          "name": "home",
          "purpose": "Landing page",
          "sections": ["hero", "features", "cta"]
        }
      ],
      "styling": {
        "theme": "modern",
        "primary_color": "#3B82F6",
        "secondary_color": "#64748B"
      }
    },
    "folder_path": "D:/Ai_project_landing_page/Ai_project_multi_page/Backend/webtemplates/website_20260216_141000",
    "saved_files": {
      "home.html": "D:/Ai_project_landing_page/.../home.html",
      "about.html": "D:/Ai_project_landing_page/.../about.html",
      "style.css": "D:/Ai_project_landing_page/.../style.css"
    }
  }
}
```

---

## Client Implementation

### JavaScript Example with Full Error Handling

```javascript
async function generateWebsite(description, threadId = null, messages = []) {
  const response = await fetch('/api/generate-website', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ description, thread_id: threadId, messages })
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        
        console.log(`[${data.step}] ${data.progress}%: ${data.message}`);

        // Handle counter-questions
        if (data.status === 'awaiting_input' && !data.ready) {
          console.log('Questions:', data.questions);
          const answers = await promptUserForAnswers(data.questions);
          return generateWebsite(answers, data.thread_id, data.messages);
        }

        // Handle completion
        if (data.status === 'completed' && data.ready) {
          console.log('Website generated!', data.data);
          return data.data;
        }

        // Handle errors
        if (data.status === 'failed') {
          throw new Error(data.error);
        }
      }
    }
  }
}
```

---

## Error Codes and Handling

| HTTP Code | Error Type | Description | Resolution |
|-----------|-----------|-------------|------------|
| `400` | Bad Request | Description < 10 chars | Provide longer description |
| `429` | Rate Limit | Too many requests | Wait and retry (see Retry-After header) |
| `500` | Internal Error | Workflow execution failed | Check logs, retry with different input |
| `503` | Service Unavailable | DSPy LM not configured | Contact administrator |

**Workflow-Level Errors:**
```json
{
  "step": "failed",
  "status": "failed",
  "progress": <last_progress>,
  "thread_id": "1707912345",
  "message": "Error: <human_readable_error>",
  "error": "<technical_error_message>"
}
```

---

## Advanced Features

### 1. Thread Continuity & Conversation Memory

**How it works:**
- LangGraph uses `MemorySaver` checkpointer to persist state per `thread_id`
- Each request with the same `thread_id` retrieves previous conversation state
- Enables multi-turn conversations without losing context

**Example:**
```javascript
// First request
const result1 = await fetch('/api/generate-website', {
  method: 'POST',
  body: JSON.stringify({ description: "I want a website" })
});
// Receives thread_id: "1707912345"

// Second request (same conversation)
const result2 = await fetch('/api/generate-website', {
  method: 'POST',
  body: JSON.stringify({
    description: "Name: XYZ Corp",
    thread_id: "1707912345",  // Same thread
    messages: [...]  // Full history
  })
});
```

---

### 2. Reference Website Scraping

**Automatic Detection:**
- System detects URLs in user input using regex
- Example: "I want a site like https://example.com"

**Scraping Process:**
1. Detects URL pattern in description
2. Calls web scraper service asynchronously
3. Analyzes HTML, CSS, and structure
4. Extracts:
   - Color palette (primary, secondary, accent)
   - Typography (font families, sizes, weights)
   - Layout patterns (grid, flexbox, sections)
   - Navigation structure
   - Design style (modern, minimalist, etc.)

**Integration:**
- Design insights injected into planning phase
- LLM uses reference patterns as inspiration (not copying)
- System prioritizes user's business requirements over reference site

**Example Analysis:**
```json
{
  "status": "completed",
  "url": "https://example.com",
  "colors": {
    "primary": "#3B82F6",
    "secondary": "#64748B",
    "accent": "#F59E0B"
  },
  "typography": {
    "heading_font": "Playfair Display",
    "body_font": "Inter",
    "base_size": "16px"
  },
  "layout": {
    "type": "grid",
    "max_width": "1200px",
    "sections": ["hero", "features", "testimonials"]
  }
}
```

---

### 3. Progressive Business Plan Refinement

**How it works:**
- Every iteration generates a business_plan (draft → refined → finalized)
- LLM progressively builds understanding with each user response

**Iteration 1:**
```
User: "Create website for cloud kitchen"
business_plan: "Cloud kitchen. Pages TBD, audience TBD, goal: likely online ordering"
ready: false
questions: ["What specific pages?", "Target audience?"]
```

**Iteration 2:**
```
User: "Home, menu, contact for busy professionals"
business_plan: "Cloud kitchen. Pages: home, menu, contact. Audience: busy professionals. Goal: showcase menu and orders"
ready: false
questions: ["Business name?", "Cuisine type?"]
```

**Iteration 3:**
```
User: "QuickBite, Italian cuisine, I'm ready"
business_plan: "QuickBite cloud kitchen, Italian. Pages: home (hero, features, CTA), menu (categories, items), contact (form, location). Audience: busy urban professionals 25-40. Goal: drive online orders"
ready: true
```

---

## Testing

### Test Page
```
GET /test
```
Returns interactive HTML page for testing the API endpoint.

### cURL Example
```bash
curl -X POST http://localhost:8000/api/generate-website \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Professional website for consulting firm. Pages: home, services, about, contact"
  }' \
  --no-buffer
```

---

## Performance & Optimization

### Parallel Execution
- **Image Description**: All descriptions generated concurrently (asyncio.gather)
- **Image Generation**: All DALL-E calls executed in parallel
- **Typical Time**: 30-60 seconds for complete 3-page website

### Rate Limiting
- **Requests per minute**: 60
- **Requests per hour**: 1000
- **Burst size**: 10 concurrent requests

### Caching & State Management
- **Thread State**: Persisted in memory using LangGraph's MemorySaver
- **Image Storage**: Saved to `/uploads` directory with unique filenames
- **Website Storage**: Saved to `/webtemplates` with timestamped folders

---

## Related Endpoints

- `GET /test` - Interactive test page
- `GET /api/serve-website/{folder_name}/{file_path}` - Serve generated website files
- `GET /health` - Basic health check
- `GET /health/ready` - Readiness probe (checks DSPy configuration)
- `GET /health/live` - Liveness probe
