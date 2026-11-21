# AI Director UI Specification: Creative Reasoning & Planning

## 1. AI Director Cockpit

The **AI Director Interface** provides a structured, collaborative environment where creators guide the automated production pipeline without giving up creative authority.

### Key Sections:
1. **Creative Brief Intake Drawer:**
   - Prompt input box with genre, intended platform (YouTube, Cinema, TikTok), target duration, and visual style selectors.
   - Generates structured `CreativeBrief` records.

2. **Concept Ideation Carousel:**
   - Presents 3 distinct creative concepts (e.g., Narrative Drama, Dynamic Commercial, Kinetic Stylized) with logline, synopsis, visual tone, and pacing metrics.
   - "Select Concept" button formally establishes the narrative direction.

3. **Script & Narrative Breakdown:**
   - Standard screenplay format (Scene Headings, Action Descriptions, Character Dialogue with Parentheticals).
   - In-line editing and beat markers.

4. **Visual Storyboard Grid:**
   - Shot-by-shot visual cards displaying shot number, camera angle (Extreme Close-Up, Wide, Low-Angle), camera motion (Pan, Push-In, Crane), prompt description, and preview thumbnail.

5. **Production Blueprint & Approval Center:**
   - Displays the dependency DAG of tasks to be dispatched across departments (Gen AI, 2D Animation, Editing, Audio, Grading).
   - Formal Approval Gates: creators review task breakdowns and approve execution before compute cycles or API costs are incurred.

