# =============================================================================
# EdGameClaw — AI Game-Based Learning Studio
# Created by Yuqi Hang (github.com/yh2072)
# https://github.com/yh2072/edgameclaw
# =============================================================================
"""Prompt templates for EdGameClaw pipeline. All chapters use custom_simulation only (no template mechanics).

- Knowledge chunk types (conceptual, procedural, etc.) for decomposition.
- Narrative: character design, Kishotenketsu plot, worldbuilding, pacing.
"""

from .assembler import get_theme_spec, get_theme, DEFAULT_THEME
from .i18n import get_prompt_lang_instruction, DEFAULT_LOCALE


def _load_simulation_design_guide() -> str:
    """Placeholder: simulation design guide (was from skill_loader). Return empty to rely on prompt only."""
    return ""

_CONCISE_ELEGANT_PRINCIPLE = (
    "Complete output is better than truncated. If approaching limits, close all "
    "braces and finish current blocks before adding new code. Prefer working "
    "code over exhaustive features."
)

_PIXEL_ART_CONCISE = (
    "Ensure every icon/sprite is fully closed. Use concise commands for effects. "
    "When approaching output limits, prioritize closing all blocks and avoid truncation."
)


def _budget(max_lines: int, max_chars: int, notes: str = "") -> str:
    """Return a compact output-budget warning to append to any system prompt.

    The warning tells the LLM the character / line ceiling so it self-regulates
    and avoids truncated output. Limits are generous to allow rich content.
    """
    base = (
        f"Output should not exceed {max_lines} lines / {max_chars:,} characters. "
        "When approaching limits, prioritize closing all blocks and avoid truncation."
    )
    return base + (f" {notes}" if notes else "")


def _art_direction_rules(theme: str, story_anchor: str = "") -> str:
    """Return shared art direction rules for cover and pixel art prompts."""
    theme_data = get_theme(theme)
    palette_str = ", ".join(theme_data["pixel_palette"])
    story_line = f"- Story anchor: {story_anchor}" if story_anchor else ""
    return f"""Color direction:
- Use the theme palette as the foundation: {palette_str}
- Build a richer palette with lighter/darker variants and a few related accent hues so the composition feels more vivid
- Do not reuse the same accent color everywhere; give major subjects their own dominant color family
- Keep strong contrast between foreground, midground, and background so the scene reads clearly

Style and narrative coherence:
- Keep the same visual language across icons, sprites, backgrounds, and cover art: line weight, shading approach, silhouette language, and detail density must match
- Reuse motifs from worldSetting and narrativeTheme so every asset feels like one story world
- Maintain the same emotional tone and visual motifs across the full asset set
{story_line}"""


# All chapters use custom_simulation only; no template mechanics (matching, sorting, etc.).
def _build_mechanic_schemas(_accent: str, _secondary: str, used_mechanics: list[str] | None = None) -> str:
    """Only custom_simulation is used; no template mechanic data. Return short note for minigame_data prompt."""
    if used_mechanics and any(m and m != "custom_simulation" for m in used_mechanics):
        return "(Legacy: template mechanics removed; all chapters use custom_simulation.)"
    return "All chapters use custom_simulation; simulation data is generated separately. Output {} for minigame_data."


KNOWLEDGE_TYPES = """
12 knowledge types (for precise classification of each knowledge chunk):
| Type | ID | Description | Example |
|---|---|---|---|
| Conceptual/Definition | conceptual | Terms, definitions, distinctions | "Difference between X and Y" |
| Procedural/Model | procedural | Steps, processes, formulas | "How X works" |
| Relational/Classification | relational | Taxonomies, comparisons | "What are the types of X" |
| Application/System | application | Applying knowledge in context, cause-effect | "What happens when X occurs" |
| Reasoning/Transfer | reasoning | Inference, analysis, new situations | "Derive Y from X" |
| Predictive | predictive | Predicting outcomes from a model | "Predict how X will change" |
| Synthesis | synthesis | Integrating multiple concepts | "A + B yields C" |
| Spatial/Discovery | spatial | Exploring structure, discovering information | "Where X sits in the system" |
| Ethical/Perspective | ethical | Moral reasoning, multi-angle thinking | "What should one do about X?" |
| Temporal | temporal | Sequence, timeline, flow | "What happens first?" |
| Transformational | transformational | Input→output chain, transformation | "X becomes Y through Z" |
| Constraint | constraint | Rules, boundaries, logical constraints | "Find a solution under the rules" |
"""

MECHANIC_MAPPING = """
Knowledge type → recommended mechanic mapping:
| Knowledge type | Primary mechanic | Alternatives | Rationale |
|---|---|---|---|
| Conceptual/Definition | matching | sorting, role_decision | Matching reinforces term–meaning links |
| Procedural/Model | sequencing | navigation, strategy_planning | Ordering builds stepwise understanding |
| Relational/Classification | sorting | deduction, matching | Sorting forces concept boundaries |
| Predictive | prediction | optimization, strategy_planning | Prediction builds and tests causal models |
| Synthesis | strategy_planning | optimization, prediction | Holistic planning supports schema integration |
| Application/System | optimization | balance_scale, reaction_timing | Experimentation supports systems thinking (note: each chapter has its own sim; here choose evaluation mechanic) |
| Spatial/Discovery | exploration | navigation, spatial_manipulation | Spatial encoding of structure |
| Reasoning/Transfer | deduction | strategy_planning, navigation | Reasoning from evidence supports transfer |
| Ethical/Perspective | role_decision | negotiation, strategy_planning | Role-play supports moral reasoning |
| Temporal | sequencing | reaction_timing, navigation | Ordering builds temporal schema |
| Transformational | balance_scale | optimization, strategy_planning | Dynamic tuning supports process understanding |
| Constraint | deduction | optimization, strategy_planning | Reasoning under constraints supports formal logic |
"""

DOMAIN_GUIDE = """
Top 5 recommended mechanics by domain:
| Domain | Recommended mechanics |
|---|---|
| STEM/Science | prediction, exploration, optimization, balance_scale, deduction |
| History/Society | sequencing, role_decision, negotiation, navigation, strategy_planning |
| Language/Literature | matching, reaction_timing, sorting, deduction, speed_classify |
| Math/Logic | optimization, sequencing, deduction, balance_scale, strategy_planning |
| Medicine/Health | deduction, role_decision, exploration, balance_scale, navigation |
| Business/Economics | optimization, strategy_planning, negotiation, balance_scale, role_decision |
| Arts/Music | reaction_timing, spatial_manipulation, matching, speed_classify, exploration |
| Engineering/Tech | optimization, balance_scale, spatial_manipulation, deduction, strategy_planning |
"""

ENGAGEMENT_LAYERS = """
Every minigame must include these interaction/feedback layers (built into the game template):
1. Feedback layer: Correct → particle effect + sound; Wrong → shake + hint; combo tracking
2. Progress layer: Score display, star rating (by accuracy), chapter unlock
3. Mastery layer: Accuracy percentage, wrong answers reviewable (show correct answer + explanation)
4. Discovery layer: Extra knowledge revealed when achieving full score
"""

# -- Created by Yuqi Hang (github.com/yh2072) --
# ---------------------------------------------------------------------------
# Narrative & Storytelling (from story-skills)
# ---------------------------------------------------------------------------

CHARACTER_DESIGN = """
Character design guide (based on character-management skill):

Each character must have a clear personality and narrative role:

### Mentor — Knowledge guide
- Archetype: Wise mentor
- Personality: Knowledgeable, gentle, occasionally humorous, passionate about learning
- Voice: Explains with metaphors and real-life examples; calm but not stiff
- Sample line: "It's like… imagine standing at a crossroads; each path leads to a different answer."
- Arc: From "pure teaching" to "moved by the player's growth"
- Relationship to player: mentor → student (guiding; becomes mentor-and-friend over time)

### Assistant — Curious companion
- Archetype: Ally / travel companion
- Personality: Lively, curious, asks questions, sometimes wrong but willing to try, cheers the player on
- Voice: Colloquial, exclamations and emoji-like expressions, likes analogies and wild ideas
- Sample line: "Wow! So that's how it works! What if we flipped it? Would it…"
- Arc: From "total beginner" to "learner who can generalize"
- Relationship to player: friend/confidant (companion, grows with the player)
- Relationship to mentor: student → mentor (respectful but sometimes challenges the mentor)

### Player (player character)
- Archetype: Hero / protagonist
- Setup: Curious, knowledge-seeking learner
- Referred to in dialogue as {player} for immersion
- Occasional choice-based dialogue (expressed through minigames)

### Interaction pattern
- Cycle: Mentor explains → Assistant asks/analogizes → Player practices (minigame)
- Assistant's "mistakes" create teachable moments
- Mentor's way of addressing the player shifts with familiarity (formal → warm)
"""

PLOT_STRUCTURE = """
Narrative structure guide (based on plot-structure & story-init skills):

Educational games use an adapted four-act Kishotenketsu structure—driven by discovery and understanding, not conflict:

### Four acts mapped to chapters
| Act | Chapters | Narrative role | Educational role |
|---|---|---|---|
| Ki (Introduction) | Ch 1–2 | Establish world, introduce characters, introduce theme | Core concepts via custom simulations, build knowledge scaffold |
| Sho (Development) | Ch 3–4 | Deepen understanding, expand exploration, character growth | Deeper knowledge via hands-on simulations |
| Ten (Twist) | Ch 5–6 | Surprising discovery, shift of perspective, "aha!" moment | Higher application via custom sims, cognitive breakthrough |
| Ketsu (Conclusion) | Ch 7–8 | Synthesize learning, reflect on growth, look ahead | Integration via custom simulations, knowledge transfer |

### Worldbuilding
Build an immersive narrative world from the learning topic:
- Turn abstract knowledge into concrete setting (e.g. economics → trade city-state, cell biology → micro-world kingdom)
- Each knowledge chunk maps to a "region" or "event" in the world
- Characters naturally encounter what they need to learn

### Foreshadowing
- Mentor hints at later content: "We'll go into this in more detail later…"
- Assistant drops clues: "I feel like I've seen something like this before…"
- Post-minigame reveals set up later chapters

### Pacing
- Alternate tension (minigame challenge) and relief (dialogue/cutscene)
- Per-chapter emotional arc: curiosity → challenge → satisfaction
- Vary simulation difficulty and interaction type across chapters for variety

### Ending design
- Review the whole learning journey (characters summarize growth)
- Resolve opening foreshadowing
- Leave the player with a sense of achievement and motivation to explore further
"""

WORLDBUILDING = """
Worldbuilding design guide (based on worldbuilding skill):

Each educational game has a themed world that turns abstract knowledge into an experience:

### Worlding strategy by subject
| Subject | World direction | Example |
|---|---|---|
| Natural science | Micro-world / lab adventure | "Shrink into the cell" |
| Social science | Historical setting / civilization sim | "Travel to an ancient trade city-state" |
| Math/Logic | Puzzle tower / decipher space | "Each floor unlocks a math secret" |
| Medicine/Psychology | Journey inside the body / mind garden | "Enter the brain's neural network" |
| Business/Economics | Startup sim / market adventure | "Run a small company" |
| Language/Literature | World inside a book / story maze | "Step into a book being written" |
| Engineering/Tech | Workshop / inventor studio | "Invent in a steampunk workshop" |

### Blending setting and knowledge
- Each background scene ties to a knowledge area (e.g. lab → experimental knowledge, library → theory)
- Objects in the scene hint at that chapter's content
- Scene changes mark a step up in knowledge level

### Tone consistency
- World tone aligns with theme palette (e.g. pink, cute)
- Even serious subjects are presented in a warm, approachable way ("cute lab" rather than cold lab)
- Character–world interaction feels natural
"""


def _format_personal_profile(personal_profile: dict | None) -> str:
    if not personal_profile:
        return ""
    parts = ["PLAYER PROFILE (weave naturally into the game narrative — make the story feel personal):"]
    if personal_profile.get("hobbies"):
        parts.append(f"  - Interests & Hobbies: {personal_profile['hobbies']}")
    if personal_profile.get("career_goals"):
        parts.append(f"  - Career Goals: {personal_profile['career_goals']}")
    if personal_profile.get("strengths"):
        strengths = personal_profile["strengths"]
        if isinstance(strengths, list):
            strengths = ", ".join(strengths)
        parts.append(f"  - Character Strengths: {strengths}")
    return "\n".join(parts) + "\n"


def knowledge_decomposition_prompt(
    topic: str,
    theme: str = DEFAULT_THEME,
    exclude_mechanics: list[str] | None = None,
    game_index: int = 0,
    total_games: int = 1,
    locale: str = DEFAULT_LOCALE,
    personal_profile: dict | None = None,
) -> tuple[str, str]:
    system = (
        "You are an educational game designer who decomposes topics into modules suited for interactive learning. "
        "You must strictly extract knowledge from the user-provided source; do not invent, assume, or add content not in the source. "
        "Engagement comes from presentation and interaction, not from altering the knowledge itself. "
        "Your output must be valid JSON only, with no other text or markdown."
    )

    theme_spec = get_theme_spec(theme)
    theme_data = get_theme(theme)

    # All chapters use custom simulation (sim_N); mechanic is set in code — no need to describe in prompt (saves tokens).
    diversity_instruction = """
Each chapter gets one custom simulation (sim_0, sim_1, ...). simulationHint is REQUIRED per chunk: [Interaction] — [Observable effect] — [Principle learned].
"""

    personal_profile_text = _format_personal_profile(personal_profile) if personal_profile else ""

    user = f"""Decompose the following topic into an educational game knowledge structure. Output JSON.

Topic: {topic}

{theme_spec}
{KNOWLEDGE_TYPES}
{diversity_instruction}
{CHARACTER_DESIGN}

Output JSON format:
{{
  "title": "Game title (2-6 words)", "subtitle": "Subtitle", "description": "Brief (2-3 sentences)",
  "totalChapters": "Integer 3-8 = number of chunks",
  "defaultPlayerName": "Default player name",
  "icons": ["30-40 English icon names covering core concepts, characters, processes, and objects for all chunks"],
  "worldSetting": "World setting that is a DIRECT METAPHOR for the learning content (2-3 sentences). The world's rules, geography, and conflict must mirror the core concepts being taught. E.g. photosynthesis → a world powered by light-harvesting crystals where plants are living energy towers; batch normalization → a data-stream realm where wild number-rivers must be tamed to flow at the right scale; immune system → a city-fortress where specialized guards patrol and identify invaders.",
  "characters": [
    {{"id":"mentor","name":"Name that fits the world","personality":"Socratic guide — asks probing questions rather than explaining; never lectures directly","voice":"Sample Socratic question the mentor would ask","arc":"Growth arc tied to the topic's mastery journey","role":"teacher","species":"Humanoid that fits the world (e.g. ancient light-keeper, data architect, city commander)"}},
    {{"id":"pet","name":"Pet name (short, world-appropriate)","personality":"Unconditionally encouraging cheerleader — celebrates every effort, keeps energy high","voice":"Short enthusiastic encouragement line","arc":"Grows more confident as player progresses","species":"Small creature that embodies a key concept from the topic (e.g. for photosynthesis: a tiny chloroplast spirit; for neural networks: a spark-wisp; for history: a memory-fragment)","role":"pet"}},
    {{"id":"player","name":"Player","personality":"Newcomer to this world who starts with misconceptions and gradually gains real understanding"}}
  ],
  "audioMood": "whimsical|mysterious|adventurous|warm|retro|calm|energetic",
  "narrativeTheme": "Overarching narrative theme that mirrors the learning journey (e.g. 'mastering light to restore a darkened world' for photosynthesis)",
  "levelNames": ["Level name 1 (beginner)", "Level 2", "Level 3", "Level 4", "Level 5 (master)"],
  "chunks": [
    {{
      "id": "chunk_1", "title": "Title",
      "type": "conceptual|procedural|relational|application|reasoning|predictive|synthesis|spatial|ethical|temporal|transformational|constraint",
      "content": "Core content (4-6 sentences: definition + principle + importance + example)",
      "simulationHint": "[Interaction] — [Observable effect] — [Principle learned] (required)",
      "narrativeHook": "Narrative hook (one sentence)"
    }}
  ]
}}
{personal_profile_text}
Core rules:
1. Knowledge fidelity: content must come strictly from the source; do not invent. Prefer less over more; never state false facts.
2. Language consistency: All text (title/subtitle/content/narrativeHook/worldSetting/character lines etc.) must use the same language. {get_prompt_lang_instruction(locale)}
3. Number of chunks by content depth (simple 3-4, medium 5-6, rich 7-8)
4. simulationHint is required for every chunk; describe the distinct interaction and what the player learns.
5. narrativeHooks should form a coherent story thread that maps to the learning arc chunk by chunk.
6. Pacing: Vary interaction intensity across chapters; second-to-last chapter can be the most demanding.
7. levelNames: 5 level names strongly tied to the domain (beginner to master); use domain terms, not generic "apprentice/scholar" (e.g. botany → [Seedling, Bud, Bloom, Fruit, Seed Guardian])
8. World coherence: worldSetting MUST be a metaphor for the topic — the world's conflict and rules mirror what the player is learning. Characters must feel native to this world. narrativeTheme must reflect the learning journey's emotional arc.

Output JSON only, no markdown."""

    return system, user


def dialog_script_prompt(topic: str, knowledge_json: str, theme: str = DEFAULT_THEME, locale: str = DEFAULT_LOCALE) -> tuple[str, str]:
    system = (
        "You are an educational game narrative designer who writes warm educational stories using a Kishotenketsu-style structure. "
        "Knowledge must strictly follow the content field in knowledge_json; do not invent. "
        "Output valid JSON array only; no other text or markdown."
    )

    theme_spec = get_theme_spec(theme)
    lang_rule = get_prompt_lang_instruction(locale)

    user = f"""Write the educational game dialog script from the knowledge structure. Output a JSON array.

Topic: {topic}
Language: {lang_rule}
⚠️ All dialog text, character names, prompts, etc. must use one consistent language; no mixing.

Knowledge structure:
{knowledge_json}

{theme_spec}

## Instruction types
1. Scene change: {{"type":"bg","bg":0,"chars":[{{"id":"mentor","x":25}},{{"id":"player","x":64}},{{"id":"pet","x":103}}]}}
   bg: 0-3; chars must include all three: mentor left (20-35), player center (55-70), pet right (95-110).
2. Chapter marker: {{"type":"chapter","ch":0}}
3. Dialog: {{"type":"dialog","name":"Character name","text":"Content"}}
   For "name" use the exact character name from the knowledge structure: mentor's name, pet's name, or "{{player}}" for the player. All three characters must speak; do not omit the pet.
4. Minigame: {{"type":"minigame","game":"sim_N"}} (one per chapter; N = 0-based chapter index. Every chapter uses a custom simulation only — always "sim_0", "sim_1", etc., never matching/sorting or other template names.)
5. End: {{"type":"end"}}

## Character roles (strictly enforce these in every chapter)
- **Mentor (teacher)**: Uses the Socratic method — never explains directly; instead asks probing questions that guide the player to discover the answer themselves. Examples: "What do you think would happen if…?", "Why do you suppose that is?", "Can you connect this to what we saw earlier?". Only confirms or gently redirects after the player has attempted an answer.
- **Pet (companion)**: The cheerleader. Always warm and encouraging. Celebrates every small effort ("You're doing amazing!", "I knew you could figure it out!"). Never corrects — just emotionally supports and keeps energy high.
- **Player**: Starts each chapter with a **misconception or genuine confusion** about the topic — says something that is partially or completely wrong, or asks a naive question that reveals a gap in understanding. Through the chapter's dialog and minigame, the player's thinking visibly shifts. The player's final line in the chapter should reflect a real "aha" moment.

## Per-chapter structure
bg change → chapter marker → intro dialog (player states a misconception; mentor asks a Socratic question in response; pet cheers) → knowledge exploration through Q&A → preview challenge → minigame → **post-sim reflection (4-6 lines: player reacts to what just happened, mentor asks a follow-up Socratic question, player answers with improved understanding, pet celebrates, mentor draws a conclusion)** → transition

Only **one** minigame per chapter. **Exactly three characters speak every chapter**: 8-11 dialog lines per chapter — mentor 3-4 lines (all questions or gentle redirects), pet 2-3 lines (all encouragement), player 2-3 lines (starts confused, ends with insight). Never write a chapter with only two characters.

## Core rules
1. Knowledge fidelity: Knowledge in dialog must come strictly from chunk content; do not invent
2. One minigame per chapter: game field is always "sim_N" (N = 0-based chapter index). All chapters use custom simulations only; do not use template names like exploration, matching, sorting.
3. Before minigame: Mentor asks a Socratic question that frames the challenge; player expresses doubt or a wrong assumption; pet encourages
4. After minigame: **4-6 lines minimum** — player reflects on what they experienced, mentor asks a follow-up question ("So what does that tell you about…?"), player articulates the insight, pet celebrates, mentor synthesises
5. Global narrative coherence: Each chapter references the previous; characters have arcs; foreshadowing is paid off
6. Character voice: Mentor (Socratic, questioning, never lecturing), Pet (bubbly, cheerleading, unconditionally encouraging), Player (starts with misconception → ends with insight). All three must speak.
7. Player name is "{{player}}"; mentor and pet use their "name" from the knowledge structure in every dialog line.
8. No empty dialog ("this is interesting", "ready?"); every line must carry knowledge or advance understanding
9. Emotional progression: Ki (curiosity + confusion) → Sho (deeper questioning) → Ten (surprise/breakthrough) → Ketsu (real understanding); ending echoes opening misconception and shows how far the player has come

Output JSON array only, no markdown."""

    return system, user


def pixel_art_prompt(topic: str, knowledge_json: str, icon_names: list[str] | None = None, theme: str = DEFAULT_THEME, locale: str = DEFAULT_LOCALE) -> tuple[str, str]:
    system = (
        "You are a pixel art artist who draws 16-color pixel sprites using JavaScript code. "
        "Your output must be executable JavaScript only; no markdown, code fences, or comment prose."
    )

    icon_names_list = ", ".join(icon_names) if icon_names else "(Design 30-40 icons from the topic)"
    theme_spec = get_theme_spec(theme)
    theme_data = get_theme(theme)
    palette_str = ", ".join(theme_data["pixel_palette"])
    art_rules = _art_direction_rules(theme, "All pixel art assets must feel like one coherent world and story arc.")

    user = f"""Generate all pixel art JavaScript code for the following educational game knowledge structure.

Topic: {topic}

Knowledge structure:
{knowledge_json}

{theme_spec}

Art direction:
{art_rules}

Use these canvas helpers (predefined):
- `gpx(g, x, y, c)` — draw a single pixel on context g
- `grect(g, x, y, w, h, c)` — draw a rectangle on context g

You must create a draw function for each of these icons: {icon_names_list}

Produce these global objects/arrays/functions:

### 1. ICONS object
Create a draw function for every icon name; none may be missing: {icon_names_list}
Each function signature is `function(g, w, h)`, drawing on a 16×16 canvas.

Example — a high-quality 16×16 brain icon:
```
brain: function(g, w, h) {{
  grect(g, 4, 3, 8, 10, '#e0a0b0');
  grect(g, 5, 2, 6, 1, '#e0a0b0');
  grect(g, 3, 5, 1, 6, '#e0a0b0');
  grect(g, 12, 5, 1, 6, '#e0a0b0');
  grect(g, 7, 3, 2, 10, '#c08090');
  gpx(g, 6, 5, '#c08090');
  gpx(g, 9, 7, '#c08090');
}}
```

```
window.ICONS = {{
  iconName: function(g, w, h) {{ gpx(g, 3, 4, '#ff6a9a'); ... }},
  ...
}};
```

Use 8–12 draw commands per icon for rich pixel detail.

### 2. CHAR_DRAW_FNS object
Create a sprite draw function per character, signature `function(g)`, on 24×36 canvas.
Character ids must match the characters in the knowledge structure.

Example — a high-quality 24×36 character sprite:
```
character: function(g) {{
  // Hair (top)
  grect(g, 9, 0, 6, 3, '#2a1020');
  grect(g, 8, 1, 8, 3, '#2a1020');
  grect(g, 10, 0, 4, 1, '#2a1020');
  // Face
  grect(g, 9, 4, 6, 6, '#f0d0b0');
  grect(g, 8, 5, 8, 4, '#f0d0b0');
  // Eyes
  grect(g, 9, 5, 2, 2, '#e080a0');
  grect(g, 13, 5, 2, 2, '#e080a0');
  gpx(g, 10, 6, '#3a1030');
  gpx(g, 14, 6, '#3a1030');
  // Mouth
  grect(g, 10, 8, 4, 1, '#e0a090');
  // Body
  grect(g, 7, 10, 10, 3, '#ffc0d0');
  grect(g, 6, 11, 12, 14, '#ffc0d0');
  grect(g, 9, 12, 6, 2, '#ff90b0');
  // Arms
  grect(g, 4, 12, 2, 10, '#f0d0b0');
  grect(g, 18, 12, 2, 10, '#f0d0b0');
  // Legs/Shoes
  grect(g, 8, 25, 8, 4, '#3a2030');
  grect(g, 7, 26, 10, 3, '#3a2030');
  grect(g, 7, 29, 4, 4, '#e080a0');
  grect(g, 13, 29, 4, 4, '#e080a0');
  grect(g, 7, 33, 4, 3, '#c06080');
  grect(g, 13, 33, 4, 3, '#c06080');
}}
```

```
window.CHAR_DRAW_FNS = {{
  mentor: function(g) {{ grect(g, 8, 0, 8, 8, '#ffc0d0'); ... }},
  pet: function(g) {{ /* pet sprite, non-human, rounded small creature */ }},
  player: function(g) {{ ... }}
}};
```

Each character sprite uses at least 15–25 draw commands with full structure: hair, face, eyes, mouth, body, arms, legs.

### 3. PORTRAITS object
Create a 32×32 portrait draw function per character, signature `function(g, w, h)`.
```
window.PORTRAITS = {{
  mentor: function(g, w, h) {{ grect(g, 8, 4, 16, 16, '#ffc0d0'); ... }},
  ...
}};
```

### 4. BACKGROUNDS array
Four background draw functions (no args; use global ctx on 128×96 canvas).
Backgrounds should match different themed scenes (e.g. classroom, lab, nature).
```
window.BACKGROUNDS = [
  function() {{ rect(0, 0, 128, 96, '#1a0818'); ... }},
  function() {{ ... }},
  function() {{ ... }},
  function() {{ ... }}
];
```
Use global `px(x,y,c)` and `rect(x,y,w,h,c)` for backgrounds.

Use 35–45 draw commands per background with layered scene elements.
Do not use Math.random for backgrounds; every pixel must be deterministic.

### 5. drawTitleLogo function
Draw the title logo on a 64×64 canvas, signature `function(g, w, h)`.
```
function drawTitleLogo(g, w, h) {{ grect(g, ...); ... }}
```

Important rules:
- Use the theme pixel palette: {palette_str}
- Pixel style should match theme and be detailed
- Character sprites: head, body, limbs; friendly expressions
- Draw only with gpx or grect; no other Canvas API
- Do not declare let/const/var outside the five global declarations above
- Code must run as-is; no export/import
- 8–12 draw commands per icon for rich pixel detail
- 18–25 draw commands per character sprite, full structure
- 35–45 draw commands per background with layered elements
- No Math.random for backgrounds; every pixel deterministic

Character design (convey through pixel art):
- mentor (guide): Academic attire (lab coat / scholar robe), glasses, gentle smile; steady palette (dark clothing + warm skin); book or pointer; upright; knowledgeable, warm, trustworthy
- pet (companion): Non-human! Small creature or spirit (orb, crystal, cloud cat, bird), compact (height ≤20px); bright/glow colors; round, cute, big eyes; lively, cute, attached to player
- player: Neutral, easy to project onto; friendly; open pose; slightly smaller than mentor

PORTRAITS: Clearly distinguish all three; mentor = authoritative but warm; assistant = energetic and curious.

Backgrounds by narrative act (Ki/Sho/Ten/Ketsu):
- BG 0 (Ki): Welcoming opening (classroom / hall / garden entrance), warm
- BG 1 (Sho): Exploration (lab / library / workshop), focused, discovery
- BG 2 (Ten): Special (height / depth / core), surprising, twist
- BG 3 (Ketsu): Conclusion (celebration / stars / journey home), achievement, warm farewell

Output JavaScript only; no ```javascript or other prose."""

    return system, user


# -- Created by Yuqi Hang (github.com/yh2072) --
# ---------------------------------------------------------------------------
# Split pixel art prompts — focused context for higher quality output
# ---------------------------------------------------------------------------

def pixel_art_icons_prompt(
    topic: str,
    icon_names: list[str] | None,
    theme: str = DEFAULT_THEME,
    locale: str = DEFAULT_LOCALE,
) -> tuple[str, str]:
    """Focused prompt: only generates the ICONS object (16×16 icons)."""
    system = (
        "You are a pixel art icon artist specializing in clear, meaningful 16×16 pixel icons. "
        "Your output must be executable JavaScript only; no markdown or prose. "
        " " + _PIXEL_ART_CONCISE + " "
        + _budget(280, 16_000, "8-12 commands per icon. Prefer fewer icons over truncation.")
    )

    _max_icons = 25  # cap to avoid truncation; complete > perfect
    names_to_use = (icon_names or [])[:_max_icons]
    names_list = ", ".join(names_to_use) if names_to_use else "Design 20-25 icons from the topic"
    theme_data = get_theme(theme)
    palette_str = ", ".join(theme_data["pixel_palette"])
    art_rules = _art_direction_rules(theme, "Icons should match the same world and narrative motifs as the rest of the asset set.")

    if names_to_use:
        skeleton_lines = [f"  {name}: function(g, w, h) {{ /* 6-10 commands */ }}," for name in names_to_use]
        skeleton = "window.ICONS = {{\n" + "\n".join(skeleton_lines) + "\n}};"
        cap_note = f" ({len(icon_names or [])} requested; draw only the first {len(names_to_use)}, all must be complete)" if (icon_names or []) and len(icon_names) > _max_icons else ""
    else:
        skeleton = "window.ICONS = {\n  // 20-25 icons, concise and complete\n};"
        cap_note = ""

    user = f"""Generate a pixel icon set for this educational game.

Topic: {topic}
Icon names needed: {names_list} {cap_note}

Draw helpers (predefined):
- `gpx(g, x, y, c)` — single pixel
- `grect(g, x, y, w, h, c)` — rectangle
Each icon signature: `function(g, w, h)` on 16×16 canvas.

Palette (prefer these colors): {palette_str}

Art direction:
{art_rules}

6-10 draw commands per icon; ensure:
- Shape is recognizable even at 16×16
- If icon name is emoji (e.g. ❓🎲), use quotes: '❓': function(g,w,h){{...}}
- Clear light/dark contrast (main + highlight/shadow)
- Use palette colors for consistent style

High-quality icon example (brain):
  brain: function(g, w, h) {{
    grect(g, 4, 3, 8, 10, '#e0a0b0');
    grect(g, 5, 2, 6, 1, '#e0a0b0');
    grect(g, 3, 5, 1, 6, '#e0a0b0');
    grect(g, 12, 5, 1, 6, '#e0a0b0');
    grect(g, 7, 3, 2, 10, '#c08090');
    gpx(g, 6, 5, '#c08090'); gpx(g, 9, 7, '#c08090');
    gpx(g, 4, 8, '#d09090'); gpx(g, 11, 6, '#d09090');
    grect(g, 6, 12, 4, 2, '#c08090');
    gpx(g, 8, 14, '#e0a0b0');
  }}

Output the following JavaScript only (no ``` or prose).
Follow the structure below; write concise code per icon (6-10 commands). Complete over perfect: fewer icons, all closed.

{skeleton}"""

    return system, user


def minigame_icons_prompt(
    topic: str,
    minigame_data: dict,
    existing_icons: list[str],
    theme: str = DEFAULT_THEME,
    locale: str = DEFAULT_LOCALE,
) -> tuple[str, str]:
    """Generate additional pixel art icons specifically referenced by minigame data but missing from ICONS."""
    system = (
        "You are a pixel art icon artist specializing in clear, meaningful 16×16 pixel icons. "
        "Your output must be an executable JavaScript snippet (object properties only); no markdown or prose."
    )

    referenced = set()
    for mg_key, mg_val in minigame_data.items():
        if not isinstance(mg_val, dict):
            continue
        for list_key in ("items", "pairs", "steps", "components", "nodes",
                         "defenses", "categories", "stimuli", "resources",
                         "sequences", "operations", "meters", "actions",
                         "stakeholders"):
            for entry in mg_val.get(list_key, []):
                if isinstance(entry, dict) and entry.get("icon"):
                    referenced.add(entry["icon"])
            if isinstance(mg_val.get(list_key), list):
                for entry in mg_val[list_key]:
                    if isinstance(entry, dict):
                        for sub_key in ("threats", "options"):
                            for sub in entry.get(sub_key, []):
                                if isinstance(sub, dict) and sub.get("icon"):
                                    referenced.add(sub["icon"])

    missing = sorted(referenced - set(existing_icons))
    if not missing:
        return "", ""

    theme_data = get_theme(theme)
    palette_str = ", ".join(theme_data["pixel_palette"])

    names_str = ", ".join(missing)
    stubs = "\n".join(f"  {name}: function(g, w, h) {{ /* draw {name} */ }}," for name in missing)

    user = f"""Generate extra pixel icons for the minigame. These are referenced in minigame data but not yet drawn.

Topic: {topic}
Icons to add (do not omit any): {names_str}

Draw helpers (predefined):
- `gpx(g, x, y, c)` — single pixel
- `grect(g, x, y, w, h, c)` — rectangle
Each icon signature: `function(g, w, h)` on 16×16 canvas.

Palette: {palette_str}

8-10 draw commands per icon. Output JavaScript object properties only (no const/var, no outer braces):

{stubs}"""

    return system, user


def pixel_art_chars_prompt(
    topic: str,
    knowledge_json: str,
    theme: str = DEFAULT_THEME,
    locale: str = DEFAULT_LOCALE,
) -> tuple[str, str]:
    """Focused prompt: only generates CHAR_DRAW_FNS and PORTRAITS.

    By focusing exclusively on characters, the LLM can invest full context
    in personality-driven pixel art rather than splitting attention across
    icons, backgrounds, and logos simultaneously.
    """
    system = (
        "You are a pixel art character designer who expresses distinct personality and emotion through sprites. "
        "Your output must be executable JavaScript only; no markdown or prose. "
        " " + _PIXEL_ART_CONCISE + " "
        + _budget(450, 28_000, "18-25 commands per sprite, 15-22 per portrait; no comments.")
    )

    theme_data = get_theme(theme)
    palette_str = ", ".join(theme_data["pixel_palette"])
    art_rules = _art_direction_rules(theme, "Characters should express the same story world, but each one should still have a distinct palette and silhouette.")

    import json as _json
    try:
        _kdata = _json.loads(knowledge_json) if isinstance(knowledge_json, str) else knowledge_json
    except Exception:
        _kdata = {}
    _chars_summary = _json.dumps(
        {
            "title": _kdata.get("title", topic),
            "worldSetting": _kdata.get("worldSetting", ""),
            "narrativeTheme": _kdata.get("narrativeTheme", ""),
            "topic": _kdata.get("topic", topic),
            "characters": _kdata.get("characters", []),
        },
        ensure_ascii=False, indent=2,
    ) if _kdata.get("characters") else knowledge_json[:800]

    user = f"""Generate character sprite and portrait pixel art for this educational game.

Topic: {topic}

Game world & characters (read worldSetting and narrativeTheme carefully — every character's appearance must fit this world):
{_chars_summary}

⚠️ CHARACTER APPEARANCE MUST REFLECT THE WORLD SETTING:
- If the world is a forest/nature setting → characters wear nature-themed clothing, earthy colors
- If the world is a space/sci-fi setting → characters have futuristic suits, glowing accents
- If the world is historical/ancient → characters wear period-appropriate robes, armour, or tunics
- If the world is underwater → characters have aquatic features, flowing cloth
- If the world is a lab/science setting → characters wear lab coats, goggles, gear
- The mentor's outfit must reflect their role in THIS specific world (not a generic teacher)
- The pet's species must match what was specified in the characters array (use the "species" field)
- The player must look like they belong in this world

Draw helpers (predefined):
- `gpx(g, x, y, c)` — single pixel
- `grect(g, x, y, w, h, c)` — rectangle

Palette (prefer): {palette_str}

Art direction:
{art_rules}

---

### Task 1: CHAR_DRAW_FNS — Full-body sprites (24×36 canvas)

Create a full-body sprite per character, signature `function(g)` (no w/h).
Required ids: mentor (teacher, humanoid, authoritative), pet (pet, small creature/spirit, cute and round), player (must match knowledge structure characters id).
- pet: Not humanoid! Draw a content-related small creature/spirit (e.g. light orb, crystal spirit, cloud cat), compact (height ≤24px), round and cute, glowing or fluffy.

Use **18-25 draw commands** per sprite; full structure:
- Hair (style reflects personality)
- Face (eyes, nose, mouth/expression)
- Body/clothing (outfit reflects role)
- Arms
- Legs/shoes

**Visual design — derive from the worldSetting and character descriptions above**:

**mentor (guide)**:
- Clothing/look: Must match the world setting (e.g. astronaut suit in space world, ancient robes in historical world, nature-fiber clothes in forest world). Read the character's "personality" field for visual cues.
- Pose: One hand holding a world-appropriate prop (staff, book, instrument, tool)
- Expression: Gentle smile, questioning/thoughtful gaze
- Stature: Upright, tallest of the three

**pet (companion spirit)**:
- Species: Use exactly what is specified in the characters array "species" field
- Look: Non-human creature, height ≤20px, round and compact, expressive face
- Colors: Bright glowing colors that complement the world palette
- Key: Use grect for round big eyes (white + colored pupil); head ≥40% of height

**player**:
- Clothing: Fits the world (traveller's outfit in adventure world, student uniform in academic world, explorer gear in nature world)
- Colors: Warm, not overshadowing others
- Slightly shorter than mentor; open and curious pose

⚠️ Do NOT default to generic "glasses + scholar robe" for mentor or "generic round blob" for pet — read the worldSetting and character descriptions and design accordingly.

Example (high-quality 24×36 mentor sprite — adapt colors/outfit to your world):
  mentor: function(g) {{
    grect(g, 8, 0, 8, 4, '#2a1020'); grect(g, 7, 1, 10, 3, '#2a1020');  // hair
    grect(g, 9, 4, 6, 8, '#f0d0b0'); grect(g, 7, 5, 10, 6, '#f0d0b0');  // face
    grect(g, 9, 6, 2, 2, '#3a1030'); grect(g, 15, 6, 2, 2, '#3a1030');  // eyes
    gpx(g, 10, 9, '#e0a090'); grect(g, 11, 10, 2, 1, '#e0a090');  // mouth
    grect(g, 6, 12, 12, 16, '#3a2868');  // outfit (change color/shape for your world)
    grect(g, 4, 13, 2, 12, '#f0d0b0');   // left arm
    grect(g, 18, 13, 2, 12, '#f0d0b0');  // right arm
    grect(g, 2, 20, 4, 3, '#f0d0b0');    // left hand
    grect(g, 2, 23, 5, 5, '#4a3070');    // prop (book/staff/tool)
    grect(g, 8, 28, 4, 6, '#2a1830');    // left leg
    grect(g, 12, 28, 4, 6, '#2a1830');   // right leg
    grect(g, 7, 33, 5, 3, '#1a0a18');    // left shoe
    grect(g, 13, 33, 5, 3, '#1a0a18');   // right shoe
  }}

Draw each character so they unmistakably belong to the game world described in worldSetting.

---

### Task 2: PORTRAITS — Character portraits (32×32 canvas)

Create a portrait per character, signature `function(g, w, h)`.
Portraits show face and personality; use **15-22 draw commands**.

- Mentor: "Authoritative but warm" — glasses, steady expression, visible collar
- Assistant: "Energetic and curious" — big round eyes, lively hair, bright smile
- Player: "Open and exploratory" — neutral, friendly, open expression

All three must be clearly distinct.

---

Output the following JavaScript only (no ```):

window.CHAR_DRAW_FNS = {{
  mentor: function(g) {{ /* 18-25 commands, mentor/teacher, humanoid */ }},
  pet: function(g) {{ /* 15-20 commands, pet spirit/creature, non-human, round, compact */ }},
  player: function(g) {{ /* 18-25 commands */ }}
}};

window.PORTRAITS = {{
  mentor: function(g, w, h) {{ /* 15-22 commands, authoritative and warm */ }},
  pet: function(g, w, h) {{ /* 12-18 commands, cute pet portrait */ }},
  player: function(g, w, h) {{ /* 15-22 commands */ }}
}};"""

    return system, user


def pixel_art_backgrounds_prompt(
    topic: str,
    knowledge_json: str,
    scene_descriptions: list[str],
    theme: str = DEFAULT_THEME,
    locale: str = DEFAULT_LOCALE,
) -> tuple[str, str]:
    """Focused prompt: generates BACKGROUNDS + drawTitleLogo tied to narrative acts.

    Each background gets a specific scene description derived from the game's
    worldSetting and chapter narrativeHooks, producing visuals that tell the
    story rather than generic academic scenes.
    """
    system = (
        "You are a pixel art scene artist who draws refined, narrative 128×96 background scenes in JavaScript. "
        "Your output must be executable JavaScript only; no markdown or prose. "
        " " + _PIXEL_ART_CONCISE + " "
        + _budget(470, 30_000, "35-45 commands per background, 18-25 for drawTitleLogo; no comments.")
    )

    theme_data = get_theme(theme)
    palette_str = ", ".join(theme_data["pixel_palette"])
    bg_color = theme_data["css"]["bg"]
    accent = theme_data["css"]["accent"]
    highlight = theme_data["css"]["highlight"]
    art_rules = _art_direction_rules(theme, "Backgrounds must progress through Ki / Sho / Ten / Ketsu while staying visually consistent with the cover and characters.")

    scene0 = scene_descriptions[0] if len(scene_descriptions) > 0 else "Warm opening world"
    scene1 = scene_descriptions[1] if len(scene_descriptions) > 1 else "Exploration scene full of discovery"
    scene2 = scene_descriptions[2] if len(scene_descriptions) > 2 else "Dramatic twist climax"
    scene3 = scene_descriptions[3] if len(scene_descriptions) > 3 else "Warm, satisfying ending"

    import json as _json
    try:
        _kdata = _json.loads(knowledge_json) if isinstance(knowledge_json, str) else knowledge_json
    except Exception:
        _kdata = {}
    _world_setting = _kdata.get("worldSetting", "")
    _narrative_theme = _kdata.get("narrativeTheme", "")
    _game_title = _kdata.get("title", topic)
    _chunks = _kdata.get("chunks", [])
    _narrative_hooks = [c.get("narrativeHook", "") for c in _chunks if c.get("narrativeHook")]
    _story_arc = " → ".join(_narrative_hooks[:6]) if _narrative_hooks else ""
    _chars = _kdata.get("characters", [])
    _char_names = ", ".join(
        f"{c.get('name','?')} ({c.get('role','?')}, species: {c.get('species','humanoid')})"
        for c in _chars if c.get("name")
    )

    _world_block = f"""Game title: {_game_title}
World setting: {_world_setting}
Narrative theme: {_narrative_theme}
Story arc (chapter hooks): {_story_arc}
Characters in this world: {_char_names}"""

    user = f"""Create 4 narrative pixel backgrounds and 1 title logo for this educational game.

Topic: {topic}
{_world_block}

Palette (prefer): {palette_str}
Base: {bg_color}, accent: {accent}, highlight: {highlight}

Art direction:
{art_rules}

---

### Draw helpers (predefined)
Background functions take **no parameters**; use global `px` and `rect` (not gpx/grect):
- `px(x, y, c)` — single pixel
- `rect(x, y, w, h, c)` — rectangle

---

### 4 narrative backgrounds

**BG 0 (Ki) — Opening world**:
{scene0}

**BG 1 (Sho) — Exploration**:
{scene1}

**BG 2 (Ten) — Dramatic twist**:
{scene2}

**BG 3 (Ketsu) — Conclusion**:
{scene3}

---

### Background drawing spec

Canvas: 128×96. Characters stand at bottom (y=60–96); avoid important buildings in that band.

**Layers (required)**:
1. **Sky** (y=0–45): 5–8 thin horizontal rects for gradient (dark→light)
2. **Stars/clouds** (y=0–30): 8–15 px stars or small rect clouds
3. **Midground** (y=30–65): Landmarks that define the world and mood
4. **Details** (y=40–70): Windows, doors, plants, machinery
5. **Ground/foreground** (y=65–96): Floor texture, close decoration

**35–45 draw commands per background**, including:
- Sky gradient (5–8 rects)
- Stars or clouds (6–15 px/small rects)
- 2–3 large elements (buildings, landmarks, nature)
- 8–15 details (windows, doors, plants, lights)
- Ground + floor lines (3–4 rects)

**Narrative consistency**: Each background must match its act AND the story arc above:
- BG 0 (Ki): The starting location from the story — where the player and characters first meet; warm, welcoming, matches scene0 description
- BG 1 (Sho): The exploration location — a place of discovery in this world, matches scene1 description
- BG 2 (Ten): The dramatic moment — a location of challenge or surprise in this world, stronger contrast, matches scene2 description
- BG 3 (Ketsu): The conclusion location — celebration or return, echoes BG 0 but transformed, matches scene3 description

**World-driven visual elements** (derive from the worldSetting and narrativeTheme — do NOT use generic templates):
- Read the worldSetting carefully and populate each background with landmarks, objects, and atmosphere that ONLY exist in that specific world
- The characters listed above should feel at home in these backgrounds
- Story arc hooks should be visually foreshadowed (e.g. if the story involves a crystal cave, BG 1 might show cave entrance; BG 2 might be deep inside)
- Every background should feel like it's from the SAME world and SAME story

High-quality background example (~50 commands, lab scene):
  function() {{
    rect(0, 0, 128, 10, '#0a0418'); rect(0, 10, 128, 8, '#120628');
    rect(0, 18, 128, 8, '#1a0838'); rect(0, 26, 128, 8, '#221048');
    rect(0, 34, 128, 8, '#2a1858'); rect(0, 42, 128, 6, '#321a60');
    px(8,3,'#fff'); px(22,6,'#ffd0ff'); px(38,2,'#fff'); px(52,7,'#ffd0ff');
    px(67,4,'#fff'); px(80,1,'#ffd0ff'); px(95,5,'#fff'); px(110,3,'#ffd0ff');
    px(118,8,'#fff'); px(15,9,'#ffd0ff'); px(45,11,'#fff');
    rect(0, 40, 42, 32, '#1e0c36'); rect(86, 35, 42, 37, '#1e0c36');
    rect(10, 44, 9, 26, '#ff8888'); rect(22, 44, 9, 26, '#ff8888');
    rect(90, 40, 9, 26, '#8888ff'); rect(103, 40, 9, 26, '#8888ff');
    rect(30, 52, 10, 18, '#ffd0a0');
    rect(36, 54, 56, 6, '#3a1848'); rect(36, 60, 4, 16, '#2a1030');
    rect(88, 60, 4, 16, '#2a1030');
    rect(38, 47, 14, 8, '#4a2058'); rect(40, 45, 10, 4, '#60e0ff');
    rect(40, 43, 6, 3, '#80f0ff');
    rect(57, 49, 10, 13, '#2a1030'); rect(59, 43, 6, 8, '#3a2040');
    rect(60, 41, 4, 4, '#503060'); rect(58, 47, 3, 3, '#80c0ff');
    rect(72, 52, 11, 8, '#ffd080'); rect(73, 46, 9, 7, '#ffe0a0');
    rect(74, 44, 7, 4, '#fff0c0'); px(76, 44, '#ffffff');
    rect(0, 72, 128, 24, '#12060e'); rect(0, 72, 128, 2, '#3a1848');
    rect(0, 72, 128, 1, '#5a2868'); rect(0, 73, 128, 1, '#2a1030');
    rect(15, 74, 20, 1, '#3a1848'); rect(50, 74, 30, 1, '#3a1848');
    rect(90, 74, 25, 1, '#3a1848');
  }}

---

### drawTitleLogo — Title logo (64×64 canvas)

Signature `function(g, w, h)`; use `gpx`/`grect` (with g).

Logo should:
- Show a core motif for the game theme and world (symbolic mark)
- Use theme accent ({accent}) and highlight ({highlight})
- Use 18–25 draw commands; visually refined

---

Output the following JavaScript only (no ```):

window.BACKGROUNDS = [
  function() {{ /* BG 0 Ki — 35-45 commands, scene: {scene0[:60]} */ }},
  function() {{ /* BG 1 Sho — 35-45 commands */ }},
  function() {{ /* BG 2 Ten — 35-45 commands */ }},
  function() {{ /* BG 3 Ketsu — 35-45 commands */ }}
];

function drawTitleLogo(g, w, h) {{
  /* 18-25 commands, iconic motif for the game world */
}}"""

    return system, user


def cover_art_prompt(
    topic: str,
    knowledge_json: str,
    theme: str = DEFAULT_THEME,
    locale: str = DEFAULT_LOCALE,
    scene_descriptions: list | None = None,
) -> tuple[str, str]:
    """Generates a stunning 128×96 cover art canvas function.

    The cover is saved as cover.js alongside the game HTML and rendered
    as a preview thumbnail on the course listing page.
    """
    system = (
        "You are a pixel art cover artist who creates striking, visually impactful game covers. "
        "Your output must be executable JavaScript only; no markdown or prose. "
        " " + _PIXEL_ART_CONCISE + " "
        + _budget(280, 22_000, "drawCover: 50-80 commands; no comments or extra variables.")
    )

    theme_data = get_theme(theme)
    palette_str = ", ".join(theme_data["pixel_palette"])
    accent = theme_data["css"]["accent"]
    highlight = theme_data["css"]["highlight"]
    glow = theme_data["css"].get("glow", accent)
    art_rules = _art_direction_rules(theme, "The cover must echo BG 0 and feel like the opening frame of the same story world.")

    import json as _json
    try:
        _kdata = _json.loads(knowledge_json) if isinstance(knowledge_json, str) else knowledge_json
    except Exception:
        _kdata = {}
    _cover_summary = ", ".join(filter(None, [
        _kdata.get("title", ""),
        _kdata.get("narrativeTheme", ""),
        _kdata.get("worldSetting", "")[:200] if _kdata.get("worldSetting") else "",
        _kdata.get("tone", ""),
    ])) or knowledge_json[:400]

    _scene0 = scene_descriptions[0] if scene_descriptions else None
    _scene0_block = f"\n\nOpening scene (BG 0 — your cover MUST echo this scene):\n{_scene0}" if _scene0 else ""

    user = f"""Create a striking pixel art cover for this educational game.

Topic: {topic}

Core game info (title, narrative theme, world, tone):
{_cover_summary}{_scene0_block}

Palette: {palette_str}
Accent: {accent}, highlight: {highlight}, glow: {glow}

Art direction:
{art_rules}

⚠️ Visual consistency rule: The cover must feel like it belongs in the same world as BG 0 (the opening scene above).
Use the same world landmarks, color mood, and time-of-day described in the opening scene.

---

### Cover design task

Canvas: 128×96 (same as game)

Draw helpers (with g):
- `gpx(g, x, y, c)` — single pixel
- `grect(g, x, y, w, h, c)` — rectangle

---

### Cover must achieve 5 things

1. **Strong composition, clear world**
   — Background reflects the world in worldSetting (use iconic, theme-bound scenes, not generic)

2. **Strong character presence**
   — Foreground (y=50–96): main character silhouettes (mentor + pet) with clear shapes
   — Faces forward or angled; visible presence

3. **Atmospheric sky gradient**
   — Sky (y=0–45): 6–10 thin horizontal rects for depth and drama
   — E.g. stars, sunset, sunrise, energy clouds

4. **Glow/light elements**
   — 1–2 glowing focal elements (window light, energy orb, star, flame)
   — Bright on dark for focus

5. **Rich layers, 50–80 draw commands**
   — Stars: 8–15 gpx points
   — Midground: 2–3 large elements
   — Details: windows, doors, plants, machinery
   — Foreground silhouettes + ground

---

### Narrative theme in image
From narrativeTheme, set emotional tone:
- "Journey of discovery" → glowing door/portal ahead
- "Joy of puzzle-solving" → floating puzzle pieces / mysterious device in midground
- "Power of knowledge" → radial beams from center at top
- "Exploration adventure" → distant mountains / space / ocean

---

Output the following JavaScript only (no ```):

function drawCover(g, w, h) {{
  // Striking game cover — 50-80 draw commands
  // Layers: sky gradient → stars → midground → details → foreground silhouettes → ground
}}"""

    return system, user


def minigame_data_prompt(topic: str, knowledge_json: str, icon_names: list[str] | None = None, theme: str = DEFAULT_THEME, locale: str = DEFAULT_LOCALE, used_mechanics: list[str] | None = None) -> tuple[str, str]:
    system = (
        "You are an educational game data designer who creates learning content data for minigames. "
        "⚠️ You must base all minigame data strictly on each chunk's content in the knowledge structure; "
        "do not invent concepts, terms, relations, or data not in the source. "
        "Engagement comes from interaction and question design, not from altering or adding knowledge. "
        "Your output must be valid JSON only; no other text or markdown."
    )

    icon_names_list = ", ".join(icon_names) if icon_names else "(Match the icon names from the pixel art)"
    theme_spec = get_theme_spec(theme)
    theme_data = get_theme(theme)
    accent = theme_data["css"]["accent"]
    secondary = theme_data["pixel_palette"][4] if len(theme_data["pixel_palette"]) > 4 else "#80b0e0"

    sim_guide = _load_simulation_design_guide()

    schemas_text = _build_mechanic_schemas(accent, secondary, used_mechanics)

    user = f"""Generate minigame data from the following knowledge structure.

Topic: {topic}

Knowledge structure:
{knowledge_json}

{theme_spec}

{sim_guide}

Every icon field must use one of these predefined icon names: {icon_names_list}. Do not use other names.

Output a JSON object whose keys are mechanic types and values are that minigame's data.

Data format per mechanic:

{schemas_text}

---

{ENGAGEMENT_LAYERS}

Data design requirements:
1. ⚠️ Language: {get_prompt_lang_instruction(locale)}. title, subtitle, pairs, categories, items, questions, and all text must match the knowledge structure language.
2. Output data only for mechanics used by chunks in the knowledge structure.
3. ⚠️⚠️ Knowledge fidelity (top priority): Each mechanic's data must **come strictly from** the corresponding chunk's content:
   - Correct answers, pairings, categories must match content; do not invent
   - Use the exact terms that appear in content; do not coin new terms
   - If content says "X belongs to class A", X's correct category in the game is A, not B
   - Do not add knowledge items not mentioned in content (prefer less over more)
4. icon fields reference icon names in the ICONS object (from pixel art).
5. Data must have educational value: accurate terms, clear explanations, distinct options.
6. Distractors (wrong options) should reflect common misconceptions but must be **wrong**—do not use correct knowledge from content as distractors.
7. Enough data per minigame (at least the minimum in the format) for ~1–2 minutes play.
8. Progressive difficulty: order questions/tasks from easier to harder within each minigame.

Output JSON only; no ```json or other text."""

    return system, user


# -- Created by Yuqi Hang (github.com/yh2072) --
# ---------------------------------------------------------------------------
# Step 5 (optional): Custom Simulation Code Generation
# ---------------------------------------------------------------------------

def simulation_code_prompt(
    topic: str,
    chunk_info: dict,
    chunk_index: int = 0,
    theme: str = DEFAULT_THEME,
    locale: str = DEFAULT_LOCALE,
    all_chunks: list[dict] | None = None,
) -> tuple[str, str]:
    """Single-pass prompt: generate complete simulation JavaScript directly."""
    theme_data = get_theme(theme)
    css = theme_data["css"]
    sim_name = f"sim_{chunk_index}"

    system = (
        "You are an expert educational game developer who writes HIGHLY VISUAL, "
        "INTERACTION-RICH JavaScript simulations. Each simulation is a hands-on "
        "INTERACTIVE PLAYGROUND — players drag objects, drop items into zones, "
        "connect nodes by dragging lines, rearrange elements, build structures, "
        "and see immediate animated visual feedback on a <canvas>. "
        "VISUAL FIRST: 80% canvas graphics, 20% text. Minimize text — teach through DOING. "
        "NEVER produce quizzes, multiple-choice, or card-selection games. "
        "NEVER create text-heavy layouts with long paragraphs or data tables. "
        + _CONCISE_ELEGANT_PRINCIPLE + " "
        "Output ONLY valid JavaScript — no markdown fences, no explanation text. "
        + _budget(700, 55_000,
            "4-6 data items max. Reuse helpers. No prose comments. "
            "Short, elegant code beats long, redundant code.")
    )

    sim_hint = chunk_info.get("simulationHint", "")
    hint_line = f"\nSimulation Hint: {sim_hint}" if sim_hint else ""
    custom_prompt = chunk_info.get("customPrompt", "").strip()
    custom_line = f"\n\n**User's custom instructions (follow these closely):** {custom_prompt}" if custom_prompt else ""
    narrative_hook = chunk_info.get("narrativeHook", "")
    hook_line = f"\nNarrative context: {narrative_hook}" if narrative_hook else ""

    other_sims_context = ""
    if all_chunks:
        other_hints = []
        for i, ch in enumerate(all_chunks):
            if i == chunk_index:
                continue
            h = ch.get("simulationHint", "")
            if h:
                other_hints.append(f"  sim_{i}: {h[:60]}")
        if other_hints:
            other_sims_context = (
                "\n\nOther sims (use DIFFERENT mechanic!):\n"
                + "\n".join(other_hints)
            )

    user = f"""Write a canvas-based interactive simulation for the following knowledge content.

## Knowledge Content
Topic: {topic}
Chunk Title: {chunk_info.get('title', '')}
Content: {chunk_info.get('content', '')}{hint_line}{custom_line}{hook_line}{other_sims_context}

## Interaction Types (choose the best fit — NEVER a quiz, NEVER text-heavy!)
- **Drag & Drop Sort**: Player drags labeled objects into target zones/categories on canvas. Objects snap into place with animation. (e.g., drag brain regions into correct lobes)
- **Node Connect**: Canvas shows nodes; player drags lines between them to create connections. Correct links glow, wrong ones shake. (e.g., connect causes to effects)
- **Drag to Build**: Player drags parts from a palette onto a canvas workspace to assemble a structure/process. (e.g., build a neural pathway, assemble a molecule)
- **Physics Playground**: Objects on canvas respond to physics — player drags, throws, adjusts gravity/friction and sees animated results. (e.g., throw a ball to learn projectile motion)
- **Spatial Puzzle**: Player rearranges, rotates, or fits pieces on canvas. Correct arrangement triggers animated reveal. (e.g., arrange timeline events, fit puzzle pieces)
- **Interactive Diagram**: Player clicks/drags parts of an animated diagram. Each interaction triggers animations + short tooltip. (e.g., click organ → zoom animation → 1-line fact)
- **Slider + Live Canvas**: 1-2 sliders control a VISUAL animation on canvas (NOT a text display). (e.g., slider changes wave frequency → canvas wave animates)

## Output: `registerMinigame('{sim_name}', function(ct, data) {{ ... }});`
The name MUST be exactly '{sim_name}'.

## Theme Colors
accent: {css['accent']}, highlight: {css['highlight']}, success: {css['success']}, text: {css['text']}, muted: {css['muted']}, bg: {css['bg']}, containerBg: {css['containerBg']}, border: {css['border']}, buttonBg: {css['buttonBg']}, cardBg: {css['cardBg']}

## APIs
- `Audio.playSFX('click'|'correct'|'wrong'|'complete'|'select')`
- `spawnParticles(x, y, 'sparkle'|'confetti', count)`
- `closeMiniGame()` — call when finished. Set `_mgScore` before calling.
- `makePortrait(name)` — returns canvas; use `.outerHTML` in template literals
- `GAME.theme` — color object; use `const T = GAME.theme || {{}};`

## SCREEN LAYOUT — MUST fill 768×576px container
`ct` = the full 768×576 overlay. Your root div MUST fill it:
```
<div style="width:720px;max-width:100%;margin:0 auto;padding:6px 12px;box-sizing:border-box">
  <!-- header: portrait + title, ~60px tall -->
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
    <div id="mg-portrait"></div>
    <div style="font:bold 15px PixelZH,monospace;color:{css['text']}">TITLE</div>
  </div>
  <!-- 1-line instruction, ~24px -->
  <div style="font:12px PixelZH,monospace;color:{css['muted']};margin-bottom:4px">Drag elements to the correct position</div>
  <!-- MAIN CANVAS — MUST be 680×420, fills remaining height -->
  <canvas id="sim-canvas" width="680" height="420"
    style="width:680px;height:420px;display:block;cursor:crosshair;border:1px solid {css['border']};border-radius:4px;pointer-events:auto"></canvas>
  <!-- status bar, ~28px -->
  <div id="sim-status" style="font:12px PixelZH,monospace;color:{css['text']};margin-top:4px;text-align:center"></div>
</div>
```
**Canvas 680×420 is mandatory** — it fills the screen. Never use max-width:320px or smaller.
Total layout: 60+24+420+28 = 532px < 576px. Perfect fit, no scrolling needed.

## Drag & Drop — Complete Working Pattern
```javascript
// Items to drag
const items = [
  {{id:0, label:'Concept A', x:50, y:50, w:90, h:36, placed:false}},
  // ... 4-6 items
];
// Drop zones on canvas
const zones = [
  {{id:0, label:'Zone 1', x:400, y:80, w:140, h:60, accepts:0}},
  // ... match items
];
let dragging = null, dragOx = 0, dragOy = 0;

function draw() {{
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0,0,680,420);
  // draw bg
  ctx.fillStyle = '{css['bg']}'; ctx.fillRect(0,0,680,420);
  // draw zones
  zones.forEach(z => {{
    ctx.strokeStyle = '{css['border']}'; ctx.lineWidth = 2;
    ctx.strokeRect(z.x, z.y, z.w, z.h);
    ctx.fillStyle = '{css['muted']}'; ctx.font = '12px PixelZH,monospace';
    ctx.fillText(z.label, z.x+8, z.y+20);
  }});
  // draw items
  items.forEach(it => {{
    if (it.placed) return;
    ctx.fillStyle = it === dragging ? '{css['accent']}' : '{css['buttonBg']}';
    ctx.fillRect(it.x, it.y, it.w, it.h);
    ctx.fillStyle = '{css['text']}'; ctx.font = '13px PixelZH,monospace';
    ctx.fillText(it.label, it.x+8, it.y+22);
  }});
}}

function getPos(e) {{
  const r = canvas.getBoundingClientRect();
  const scaleX = 680 / r.width, scaleY = 420 / r.height;
  const src = e.touches ? e.touches[0] : e;
  return {{x: (src.clientX - r.left) * scaleX, y: (src.clientY - r.top) * scaleY}};
}}
canvas.addEventListener('mousedown', e => {{
  const p = getPos(e);
  dragging = items.find(it => !it.placed && p.x>=it.x && p.x<=it.x+it.w && p.y>=it.y && p.y<=it.y+it.h) || null;
  if (dragging) {{ dragOx = p.x - dragging.x; dragOy = p.y - dragging.y; }}
}});
canvas.addEventListener('mousemove', e => {{
  if (!dragging) return;
  const p = getPos(e);
  dragging.x = p.x - dragOx; dragging.y = p.y - dragOy; draw();
}});
canvas.addEventListener('mouseup', e => {{
  if (!dragging) return;
  const p = getPos(e);
  const hit = zones.find(z => p.x>=z.x && p.x<=z.x+z.w && p.y>=z.y && p.y<=z.y+z.h);
  if (hit && hit.accepts === dragging.id) {{
    dragging.placed = true; dragging.x = hit.x+25; dragging.y = hit.y+12;
    Audio.playSFX('correct'); spawnParticles(hit.x+70, hit.y+30, 'sparkle', 6);
    // check complete
    if (items.every(it => it.placed)) {{ _mgScore = 100; Audio.playSFX('complete'); spawnParticles(340, 210, 'confetti', 30); showResults(); }}
  }} else {{ Audio.playSFX('wrong'); }}
  dragging = null; draw();
}});
// Mirror touch events
canvas.addEventListener('touchstart', e=>{{e.preventDefault();canvas.dispatchEvent(new MouseEvent('mousedown',{{clientX:e.touches[0].clientX,clientY:e.touches[0].clientY}}));}}, {{passive:false}});
canvas.addEventListener('touchmove',  e=>{{e.preventDefault();canvas.dispatchEvent(new MouseEvent('mousemove',{{clientX:e.touches[0].clientX,clientY:e.touches[0].clientY}}));}}, {{passive:false}});
canvas.addEventListener('touchend',   e=>{{e.preventDefault();canvas.dispatchEvent(new MouseEvent('mouseup',  {{clientX:(e.changedTouches[0]||{{}}).clientX||0,clientY:(e.changedTouches[0]||{{}}).clientY||0}}));}}, {{passive:false}});
// showResults: always call this when game is complete — replaces ct with a continue screen
function showResults() {{
  ct.innerHTML = `<div style="text-align:center;padding:40px 20px;font-family:'PixelZH',monospace">
    <div style="color:{css['success']};font-size:28px;margin-bottom:8px">✓ Complete!</div>
    <div style="color:{css['muted']};font-size:13px;margin-bottom:24px">${{items.filter(it=>it.placed).length}}/${{items.length}} correct</div>
    <button id="done" class="mg-btn" style="pointer-events:auto;padding:12px 32px;font-size:14px;border-color:{css['success']};color:{css['success']}">Continue →</button>
  </div>`;
  var btn = ct.querySelector('#done');
  if (btn) btn.addEventListener('click', function() {{ closeMiniGame(); }});
}}
```

## VISUAL-FIRST Rules
- Canvas 680×420 is your primary display — draw ALL content on it (items, zones, connections, diagrams)
- 4-6 items MAX, short labels (2-4 words). NO paragraphs, NO long descriptions
- ALL educational content via visual metaphor + interaction, NOT text blocks
- `data` may be empty `{{}}` — NEVER use `data.title`, `data.subtitle`, `data.portrait` directly; always use `data.title||'Title'`, `data.subtitle||''`, `makePortrait(data.portrait||'mentor')`; ALL game content MUST be hardcoded as const arrays/objects
- Set `ct.innerHTML = html`, then `var btn = ct.querySelector('#id'); if (btn) btn.addEventListener('click', fn);` — NEVER use `ct.querySelector('#id').addEventListener` directly (throws if null)
- All interactive elements need `pointer-events:auto`
- NEVER use `100vw/100vh`, `document.getElementById()`, absolute positioning for UI panels
- Font: `'PixelZH','Courier New',monospace`. Min font: 12px. NEVER dark grays (#333-#888)
- CANVAS TEXT CONTRAST: labels on colored shapes MUST be legible — draw a dark semi-transparent strip first: `g.fillStyle='rgba(0,0,0,0.55)'; g.fillRect(x, y+h-14, w, 14);` then draw white text on top. NEVER draw text in a color similar to the shape beneath it.
- No semicolons inside template literal `${{}}` expressions
- {get_prompt_lang_instruction(locale)}
- Completion screen: 2-3 bullet points + Continue button → closeMiniGame()
- Continue button MUST always be reachable regardless of score
- Code must be complete and functional — concise over verbose, no stubs
- TOKEN BUDGET: Output MUST fit within ~14000 tokens. Write concise code — no redundant comments, no verbose names, extract repeated draw calls into helper functions. Truncated/incomplete code causes runtime failures and is worse than shorter working code.

## CRITICAL: Animation Loop Safety (prevents game freeze)
- NEVER assign `window.spawnParticles = ...` or override ANY global function
- requestAnimationFrame loops MUST check `if (!ct.querySelector('#sim-canvas')) {{ _rafId = null; return; }}`
- Track rAF IDs: `let _rafId = null;` then `_rafId = requestAnimationFrame(loop);`
- Before starting a new loop, cancel existing: `if (_rafId) {{ cancelAnimationFrame(_rafId); _rafId = null; }}`
- getPos() MUST apply scale: `const scaleX = 680/r.width; const scaleY = 420/r.height;`
- NEVER use `splice()` inside a `forEach`/`for` loop — use `array = array.filter(...)` instead to avoid undefined holes
- In the animation loop, ALWAYS guard array access: `items.forEach(it => {{ if (!it) return; ... }})` — prevents "Cannot read properties of undefined"
- Particle removal: use `particles = particles.filter(p => p && p.life > 0);` NOT `particles.splice(...)`

## FORBIDDEN (auto-rejected)
- ❌ Multiple-choice / picking A/B/C / quiz Q&A
- ❌ Card-selection / clicking cards to read text
- ❌ Canvas smaller than 600px wide — ALWAYS use 680×420
- ❌ Text walls: paragraphs > 2 lines, data tables, long descriptions
- ❌ Sliders as the ONLY interaction (must combine with canvas drag or direct manipulation)
- ❌ Broken drag: always implement mousedown+mousemove+mouseup+touch mirror

Output ONLY JavaScript code. No markdown. No explanation."""

    return system, user


def sim_regen_from_existing_prompt(
    existing_code: str,
    chunk_info: dict,
    chunk_index: int = 0,
    theme: str = DEFAULT_THEME,
    locale: str = DEFAULT_LOCALE,
    custom_prompt: str = "",
) -> tuple[str, str]:
    """Prompt for regenerating a simulation by revising existing code. Links original code + design so the model can modify in place."""
    theme_data = get_theme(theme)
    css = theme_data["css"]
    sim_name = f"sim_{chunk_index}"
    # Keep existing code in context but cap size to avoid token overflow
    max_code = 28_000
    if len(existing_code) > max_code:
        existing_code = existing_code[: max_code - 80] + "\n\n// ... [truncated for context] ..."
    custom_line = f"\n\n**User's instructions (apply these):** {custom_prompt}" if custom_prompt.strip() else ""
    lang_rule = get_prompt_lang_instruction(locale)

    system = (
        "You are an expert JavaScript developer. You are REVISING an existing educational simulation. "
        "The user has the current code below and wants to regenerate/improve it. "
        "PRESERVE the existing structure, variable names, and patterns where they work well. "
        "APPLY the user's instructions: simplify, add steps, change labels, fix bugs, or adjust difficulty. "
        "Output MUST be a COMPLETE, valid registerMinigame('" + sim_name + "', function(ct, data) { ... }); block. "
        "No markdown fences. No explanation. Same APIs: Audio.playSFX, spawnParticles, closeMiniGame, makePortrait, GAME.theme. "
        "Canvas 680×420. Keep drag/touch events and null-checks. "
        + _CONCISE_ELEGANT_PRINCIPLE
    )

    user = f"""Revise the following simulation code. Keep the same mechanic and style unless the user asks to change them.

## Current simulation code (link / base for revision)
```javascript
{existing_code}
```

## Knowledge context
Title: {chunk_info.get('title', '')}
Content: {chunk_info.get('content', '')[:800]}
{custom_line}

## Theme colors (use these)
accent: {css['accent']}, highlight: {css['highlight']}, success: {css['success']}, muted: {css['muted']}, border: {css['border']}, cardBg: {css['cardBg']}

## Rules
- Output ONLY the full registerMinigame('{sim_name}', function(ct, data) {{ ... }}); code. No other text.
- Preserve existing structure and logic where the user did not ask to change it.
- All labels/instructions must follow: {lang_rule}
- Code must be complete and runnable (no stubs, no truncation).
"""

    return system, user


# -- Created by Yuqi Hang (github.com/yh2072) --
# ---------------------------------------------------------------------------
# Two-phase simulation generation prompts
# ---------------------------------------------------------------------------

def sim_design_prompt(
    topic: str,
    chunk_info: dict,
    chunk_index: int = 0,
    theme: str = DEFAULT_THEME,
    locale: str = DEFAULT_LOCALE,
    all_chunks: list[dict] | None = None,
) -> tuple[str, str]:
    """Phase 1: Design an experiment-like simulation blueprint (no code)."""
    theme_data = get_theme(theme)
    css = theme_data["css"]

    other_mechanics = ""
    if all_chunks:
        others = []
        for i, ch in enumerate(all_chunks):
            if i == chunk_index:
                continue
            h = ch.get("simulationHint", "")
            if h:
                others.append(f"  sim_{i}: {h[:80]}")
        if others:
            other_mechanics = (
                "\n\nOther simulations in this game (AVOID duplicating their mechanics):\n"
                + "\n".join(others)
            )

    sim_hint = chunk_info.get("simulationHint", "")
    hint_line = f"\nDesired interaction style: {sim_hint}" if sim_hint else ""
    custom_prompt = chunk_info.get("customPrompt", "").strip()
    custom_line = f"\n\n**User's custom instructions (follow these closely):** {custom_prompt}" if custom_prompt else ""

    system = (
        "You are an expert educational game designer specializing in HIGHLY VISUAL, "
        "INTERACTION-RICH simulations. You design hands-on INTERACTIVE PLAYGROUNDS — "
        "players DRAG objects into zones, CONNECT nodes by drawing lines, BUILD structures "
        "from parts, REARRANGE elements spatially, and see animated visual feedback. "
        "Your designs are 80% VISUAL (canvas graphics) and 20% text (short labels only). "
        "NEVER design quizzes, text-heavy layouts, or slider-only interactions. "
        "Teach through DOING and SEEING, not through reading paragraphs. "
        "Output ONLY plain text (no JSON, no code). A developer will use your description to write the simulation code."
    )

    lang_rule = get_prompt_lang_instruction(locale)

    user = f"""Design an interactive EXPERIMENT simulation for the following content. Write a clear TEXT description only (no JSON, no code).

## Knowledge Content
Chunk Title: {chunk_info.get('title', '')}
Knowledge Type: {chunk_info.get('type', '')}
Content: {chunk_info.get('content', '')}{hint_line}{custom_line}{other_mechanics}

⚠️ Language rule: {lang_rule}

## INTERACTION PATTERNS — pick one (visual-first, minimal text!)

### Pattern A: DRAG & DROP SORT — Player drags labeled objects into target zones on canvas
Example: "Brain Map" — canvas shows brain outline with labeled regions. Player drags small icons from a palette onto the correct brain region. Correct drops glow + snap; wrong drops bounce back.
Key: 4-8 draggable items, 3-5 drop zones. Items are VISUAL (colored circles/icons with 1-2 word labels).

### Pattern B: NODE CONNECT — Player drags lines between nodes on canvas
### Pattern C: DRAG TO BUILD — Player drags parts from a palette onto a canvas workspace
### Pattern D: SPATIAL PUZZLE — Player rearranges pieces on canvas
### Pattern E: INTERACTIVE DIAGRAM — Player taps parts of an animated canvas diagram
### Pattern F: PHYSICS PLAYGROUND — Objects have simple physics; player manipulates them

## FORBIDDEN: quizzes, multiple-choice, flashcards, matching exercises, text-heavy UI.

## Output (plain text only)

In 1–2 short paragraphs, describe:
1. **Mechanic**: What the player physically DOES (e.g. drag items to zones, connect nodes, build a timeline).
2. **Title**: Evocative 2–4 word title for the simulation.
3. **Instruction**: One imperative sentence for the player (e.g. "Drag each icon to the correct region").
4. **Canvas**: What is DRAWN on the main 680×420 canvas (shapes, diagram, zones, palette).
5. **Items**: 4–8 draggable or interactive elements with SHORT labels (1–4 words each).
6. **Flow**: Steps (e.g. player drags → correct drop animates → score + Continue).
7. **Feedback**: What animation on correct/wrong (glow, snap, shake).

Keep labels and terminology from the knowledge content. No JSON, no code — prose only."""

    return system, user


def sim_implement_prompt(
    design_text: str,
    chunk_info: dict,
    chunk_index: int = 0,
    theme: str = DEFAULT_THEME,
    locale: str = DEFAULT_LOCALE,
) -> tuple[str, str]:
    """Phase 2: Implement JavaScript code from a plain-text design description."""
    theme_data = get_theme(theme)
    css = theme_data["css"]
    sim_name = f"sim_{chunk_index}"

    system = (
        "You are an expert JavaScript developer who builds HIGHLY VISUAL, "
        "INTERACTION-RICH canvas simulations. You receive a design description (plain text) and "
        "produce a COMPLETE registerMinigame() call with: "
        "- Canvas 2D rendering as the PRIMARY UI (80% of screen) "
        "- DRAG-AND-DROP: mousedown/mousemove/mouseup + touch events for direct object manipulation "
        "- Animated visual feedback: snap, glow, shake, particle burst on every action "
        "- MINIMAL TEXT: only short labels (1-4 words) and 1-line instruction "
        "- NO text paragraphs, NO data tables, NO long descriptions in the UI "
        "- PIXEL ART OBJECTS: draw all objects using ctx.fillRect/arc/fillText — absolutely NO emoji (❌🔴⭐) on canvas "
        "- CLARITY: the simulation MUST clearly demonstrate ONE specific concept — no abstract, confusing or purposeless mechanics "
        "- Use drawXxx() helper functions (provided via visual_helpers) to render recognizable pixel art shapes "
        "- Any queried DOM element must be stored in a variable and null-checked before addEventListener; never chain addEventListener directly from querySelector/getElementById. "
        + _CONCISE_ELEGANT_PRINCIPLE + " "
        "Output ONLY valid JavaScript. No markdown fences. No explanation text. "
        + _budget(700, 55_000,
            "4-6 data items max. Reuse helpers. No prose comments. "
            "Short, elegant code beats long, redundant code.")
    )

    user = f"""Implement the following simulation design as COMPLETE JavaScript code.

## Design Blueprint (plain text description)
{design_text}

## Knowledge Context
Title: {chunk_info.get('title', '')}
Content: {chunk_info.get('content', '')}
⚠️ Language: {get_prompt_lang_instruction(locale)} — all labels, buttons, hints, and instructions must follow this language

## REFERENCE: How a HIGH-QUALITY drag-and-drop simulation looks (condensed)

```
registerMinigame('sim_N', function(ct, data) {{
  const T = GAME.theme || {{}};
  const accent = T.accent || '#ff6a9a';
  // ... theme colors

  // Items: SHORT labels, visual properties, positions
  const items = [
    {{ id: 0, label: 'Short label', x: 30, y: 300, w: 60, h: 30, color: accent, placed: false }},
    // ... 4-8 items with 1-4 word labels
  ];
  const dropZones = [
    {{ id: 0, label: 'Zone name', x: 100, y: 50, w: 80, h: 60, accepts: [0, 1] }},
    // ... 3-5 zones
  ];
  let dragging = null, dragOX = 0, dragOY = 0, score = 0;
  let _rafId = null;
  let particles = [];

  function drawCanvas() {{
    const c = ct.querySelector('#sim-canvas');
    if (!c) return;
    const g = c.getContext('2d');
    g.clearRect(0, 0, 680, 420);
    // Draw drop zones (highlighted rectangles with labels)
    dropZones.forEach(z => {{
      g.fillStyle = z.active ? 'rgba(100,255,100,0.2)' : 'rgba(255,255,255,0.05)';
      g.fillRect(z.x, z.y, z.w, z.h);
      g.strokeStyle = border; g.strokeRect(z.x, z.y, z.w, z.h);
      g.fillStyle = muted; g.font = '11px "PixelZH",monospace';
      g.fillText(z.label, z.x + 4, z.y + z.h/2 + 4);
    }});
    // Draw draggable items (colored shapes with short labels)
    items.forEach(it => {{
      g.fillStyle = it.placed ? success : it.color;
      g.fillRect(it.x, it.y, it.w, it.h);
      g.fillStyle = '#fff'; g.fillText(it.label, it.x + 4, it.y + it.h/2 + 4);
    }});
    // Draw particles for feedback
    particles.forEach(p => {{ /* animated sparkles */ }});
  }}

  ct.innerHTML = `<div style="width:720px;max-width:100%;margin:0 auto;padding:6px 12px;box-sizing:border-box;font-family:'PixelZH',monospace">
    <p style="color:${{T.muted}};font-size:12px;margin:0 0 4px">Drag elements to the correct position</p>
    <canvas id="sim-canvas" width="680" height="420"
      style="width:680px;height:420px;display:block;border-radius:4px;pointer-events:auto;cursor:grab"></canvas>
    <div id="sim-score" style="color:${{T.highlight}};font-size:12px;margin-top:4px;text-align:center">0/${{items.length}}</div>
  </div>`;

  const canvas = ct.querySelector('#sim-canvas');
  canvas.addEventListener('mousedown', function(e) {{
    const r = canvas.getBoundingClientRect();
    const mx = (e.clientX - r.left) * 680 / r.width;
    const my = (e.clientY - r.top) * 420 / r.height;
    for (let i = items.length - 1; i >= 0; i--) {{
      const it = items[i];
      if (!it.placed && mx >= it.x && mx <= it.x+it.w && my >= it.y && my <= it.y+it.h) {{
        dragging = it; dragOX = mx - it.x; dragOY = my - it.y;
        canvas.style.cursor = 'grabbing'; break;
      }}
    }}
  }});
  canvas.addEventListener('mousemove', function(e) {{
    if (!dragging) return;
    const r = canvas.getBoundingClientRect();
    dragging.x = (e.clientX - r.left) * 680 / r.width - dragOX;
    dragging.y = (e.clientY - r.top) * 420 / r.height - dragOY;
    drawCanvas();
  }});
  canvas.addEventListener('mouseup', function() {{
    if (!dragging) return;
    // Check drop zones, snap or bounce back
    canvas.style.cursor = 'grab'; dragging = null; drawCanvas();
  }});
  // Touch equivalents: touchstart, touchmove, touchend

  drawCanvas();

  function showResults() {{
    ct.innerHTML = `<div style="text-align:center;padding:20px">
      <h3 style="color:${{T.highlight}}">✓ Complete</h3>
      <p style="color:${{T.text}};font-size:12px">Score: ${{score}}/${{items.length}}</p>
      <button id="done" style="padding:12px 24px;background:${{T.accent}};color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:14px">Continue</button>
    </div>`;
    var btn = ct.querySelector('#done');
    if (btn) btn.addEventListener('click', function() {{ _mgScore = score; closeMiniGame(); }});
  }}
}});
```

## Theme Colors
accent: {css['accent']}, highlight: {css['highlight']}, success: {css['success']}, text: {css['text']}, muted: {css['muted']}, bg: {css['bg']}, containerBg: {css['containerBg']}, border: {css['border']}, buttonBg: {css['buttonBg']}, cardBg: {css['cardBg']}

## Output: `registerMinigame('{sim_name}', function(ct, data) {{ ... }});`
The name MUST be exactly '{sim_name}'.

## APIs
- `Audio.playSFX('click'|'correct'|'wrong'|'complete'|'select')`
- `spawnParticles(x, y, 'sparkle'|'confetti', count)`
- `closeMiniGame()` — call when finished. XP and stars are based on performance: set global `_mgScore` (0–100) before calling, e.g. `_mgScore = Math.round((score / maxScore) * 100); closeMiniGame();` so the engine can award XP.
- `makePortrait(name)` — returns canvas element; use `.outerHTML` in template literals
- `GAME.theme` — color object, use safe access with defaults

## Rules (compact)
- TOKEN BUDGET: Your entire output MUST fit within ~18000 tokens. Write CONCISE code — no redundant comments, no verbose variable names, no repeated logic. Use helper functions to DRY up repeated draw calls. If you find yourself writing the same pattern more than twice, extract it into a function. Incomplete/truncated code causes runtime failures.
- VISUAL FIRST: canvas is 80% of UI. Text is minimal — 1-line instruction + short labels only
- Data arrays: 4-8 items MAX with 1-4 word labels. NO paragraphs. NO long text content hardcoded.
- `data` may be empty `{{}}` — use `data.title||'Title'`, `data.subtitle||''`, `makePortrait(data.portrait||'mentor')`; ALL game content MUST be hardcoded
- Render via `ct.innerHTML`, listeners via `ct.querySelector().addEventListener()`
- All interactive elements need `pointer-events:auto`
- `ct` is 768×576px. Root: `width:720px;max-width:100%;margin:0 auto;padding:6px 12px;box-sizing:border-box`
- Canvas: MUST be `width="680" height="420"` with CSS `width:680px;height:420px;display:block` — fills the screen. NEVER max-width:320px or smaller.
- NEVER use `100vw/100vh`, `document.getElementById()`, inline onclick
- Listeners: `var btn = ct.querySelector('#id'); if (btn) btn.addEventListener('click', fn);` — NEVER `ct.querySelector('#id').addEventListener(...)` directly (throws if element is null)
- window.addEventListener and document.addEventListener are allowed, but queried elements must still be null-checked before binding
- Font: `'PixelZH','Courier New',monospace`. Min size: 12px
- Text colors: theme.text for body, theme.highlight for titles. NEVER dark grays (#333-#888)
- CANVAS TEXT CONTRAST: labels on colored shapes MUST be legible — draw a dark semi-transparent strip first: `g.fillStyle='rgba(0,0,0,0.55)'; g.fillRect(x, y+h-14, w, 14);` then draw white text. NEVER draw text in a color similar to the shape background.
- No semicolons inside template literal `${{}}` expressions
- Continue button MUST always be reachable regardless of score
- Code must be CONCISE and complete: minimal lines for maximum visual/interaction impact

## Drag Implementation (MUST include for drag-based designs)
- Canvas coordinates: `const r = canvas.getBoundingClientRect(); const mx = (e.clientX - r.left) * 680 / r.width; const my = (e.clientY - r.top) * 420 / r.height;`
- Touch: add `touchstart`/`touchmove`/`touchend` listeners with `e.touches[0]` and `e.preventDefault()`
- Hit test: check if mouse is inside object bounds
- Drop zone check: test overlap between dragged item and zone rectangles
- Feedback: snap animation (lerp to target), shake animation (oscillate x), glow (draw with shadowBlur)

## CRITICAL: Animation Loop Safety (prevents game freeze)
- NEVER assign `window.spawnParticles = ...` or override ANY global function
- requestAnimationFrame loops MUST check `if (!ct.querySelector('#your-element')) {{ _rafId = null; return; }}`
- Track rAF IDs: `let _rafId = null;` then `_rafId = requestAnimationFrame(loop);`
- Before starting a new loop, cancel existing: `if (_rafId) {{ cancelAnimationFrame(_rafId); _rafId = null; }}`
- NEVER use `splice()` inside a `forEach`/`for` loop — use `array = array.filter(...)` instead to avoid undefined holes
- In the animation loop, ALWAYS guard array access: `items.forEach(it => {{ if (!it) return; ... }})` — prevents "Cannot read properties of undefined"
- Particle removal: use `particles = particles.filter(p => p && p.life > 0);` NOT `particles.splice(...)`

Output ONLY JavaScript code. No markdown fences. No explanation."""

    return system, user


# ---------------------------------------------------------------------------
# Simulation Judge & Refine prompts
# ---------------------------------------------------------------------------

def sim_judge_prompt(
    code: str,
    chunk_info: dict,
    chunk_index: int,
) -> tuple[str, str]:
    """LLM judge: evaluate simulation educational quality and interaction richness."""
    system = (
        "You are an expert educational game critic. Evaluate JavaScript simulations strictly "
        "for educational effectiveness, interaction richness, and visual quality. "
        "Be specific and brutally honest. Output ONLY valid JSON, no markdown."
    )

    code_preview = code[:10000] + ("\n// ...(truncated)" if len(code) > 10000 else "")

    user = f"""Evaluate this educational simulation.

## Learning Objective
Title: {chunk_info.get('title', '')}
Content: {chunk_info.get('content', '')}
Interaction Hint: {chunk_info.get('simulationHint', '')}

## Simulation Code (sim_{chunk_index})
```javascript
{code_preview}
```

## Score each dimension 0-25 (BE HARSH — most simulations score 12-18, not 20+):

1. **Educational Alignment** (0-25)
   - Does the player physically DO the core concept (drag neurons to connect, assemble a process, sort elements)?
   - Or are they just reading text / clicking buttons to see information?
   - High score (20+): interaction IS the learning mechanic — player cannot pass without understanding the concept.
   - Medium (12-19): some interaction but concept could be learned by clicking randomly.
   - Low (≤11): interaction is just navigation/reading. DEDUCT 12 pts if concept is confusing or player can't understand within 5 seconds.

2. **Visual Richness & Contrast** (0-25)
   - Are objects drawn as recognizable pixel art shapes using fillRect/arc (NOT emoji)?
   - Are concepts drawn as meaningful diagrams (brain outline, molecule, timeline, flowchart, circuit)?
   - High score (20+): canvas has rich pixel art — shapes clearly represent the educational concept.
   - Medium (12-19): colored boxes with text labels, no meaningful visual metaphor.
   - Low (≤11): plain boxes only OR emoji used on canvas.
   - DEDUCT 20 pts if ANY emoji characters (🔴⭐🌱🧠) appear drawn on canvas via fillText.
   - DEDUCT 10 pts if canvas is mostly empty / only 2-3 colored rectangles with no educational visual metaphor.
   - COLOR CONTRAST (critical for readability): DEDUCT 12 pts if text color is too similar to background (e.g. white text on light background, dark text on dark background, gray text on gray). Minimum contrast: text must be clearly readable. Common failures: fillStyle='#fff' then drawing on white/light bg; fillStyle='#333' on dark bg; using theme.muted color for important labels.
   - DEDUCT 8 pts if label text is drawn directly on colored shapes without a contrasting background strip or outline (text must always be legible against the shape beneath it).

3. **Interaction Quality** (0-25)
   - Is the primary mechanic drag-and-drop, node-connect, draw, or spatial building? (HIGH 20+)
   - Multiple sliders as main interaction: score ≤14.
   - Only buttons/clicks with no canvas interaction: score ≤10.
   - Is feedback animated (snap, glow, shake, particle burst on correct)? Required for 18+.
   - DEDUCT 8 pts if touch events are missing (touchstart/touchmove/touchend).

4. **Completability & Runtime Safety** (0-25)
   - Can the player ALWAYS reach the completion screen (no stuck states, no score requirements to proceed)?
   - Is the canvas EXACTLY 680×420px? DEDUCT 10 if different.
   - Does the code use `array.filter()` for removal (not `splice` inside loops)? DEDUCT 8 if splice in loops detected.
   - Does the animation loop guard `if (!ct.querySelector(...)) return`? DEDUCT 8 if missing.
   - Are there obvious runtime errors (accessing `.x` on undefined, uninitialized vars)? DEDUCT 15 if yes.

Output JSON:
{{
  "scores": {{"educational": 0, "visual": 0, "interaction": 0, "completable": 0}},
  "total": 0,
  "approved": false,
  "critical_issues": ["specific bug or design flaw — be concrete, e.g. 'particles.splice inside forEach will cause undefined.x crash'"],
  "visual_improvements": ["specific canvas drawing change, e.g. 'draw cell membrane using arc at x=340,y=210 r=120'"],
  "interaction_improvements": ["specific mechanic change, e.g. 'replace slider with drag-to-connect nodes'"],
  "clarity_issues": ["if concept is confusing, describe what's unclear and how to fix it"]
}}

approved = true only if total >= 82. Default to strict — a simulation needs to genuinely teach through interaction, not just display information."""

    return system, user


def sim_refine_prompt(
    code: str,
    judge_feedback: dict,
    chunk_info: dict,
    chunk_index: int,
    theme: str = DEFAULT_THEME,
    locale: str = DEFAULT_LOCALE,
) -> tuple[str, str]:
    """Refine simulation code based on judge feedback."""
    import json as _json
    theme_data = get_theme(theme)
    css = theme_data["css"]
    sim_name = f"sim_{chunk_index}"
    feedback_str = _json.dumps(judge_feedback, ensure_ascii=False, indent=2)

    system = (
        "You are an expert JavaScript developer. You receive simulation code and judge feedback. "
        "Your task: rewrite the simulation to fix ALL critical issues and implement the top improvements. "
        "KEEP: same registerMinigame name, same core educational concept. "
        "IMPROVE: visuals (pixel art shapes not rectangles), interactions (drag > sliders), canvas size (680×420). "
        "PIXEL ART RULE: draw ALL objects using ctx.fillRect/arc/bezierCurveTo — NEVER use emoji on canvas. "
        "CLARITY RULE: one clear concept, player understands immediately what to do and why. "
        "Fix only the failing areas; preserve structure where possible and avoid introducing new globals. "
        "Any queried DOM element must be stored in a variable and null-checked before addEventListener. "
        "Output ONLY valid JavaScript. No markdown. No explanation."
    )

    user = f"""Improve this simulation based on judge feedback. Rewrite it completely if needed.

## Judge Feedback (score={judge_feedback.get('total', '?')}/100)
{feedback_str}

## Original Code
```javascript
{code[:18000]}
```

## Mandatory Requirements
- registerMinigame name MUST be exactly '{sim_name}'
- Canvas: `<canvas id="sim-canvas" width="680" height="420" style="width:680px;height:420px;display:block;pointer-events:auto">`
- Root: `<div style="width:720px;max-width:100%;margin:0 auto;padding:6px 12px;box-sizing:border-box">`
- Fix ALL critical_issues listed above
- Fix ALL clarity_issues: ensure the concept and player action are immediately obvious
- Implement ALL visual_improvements using pixel art (fillRect/arc) — NO emoji on canvas
- Implement the top 2 interaction_improvements
- Educational concept to teach: {chunk_info.get('title', '')} — {chunk_info.get('content', '')[:300]}
- Language: {get_prompt_lang_instruction(locale)}
- Theme: accent={css['accent']}, text={css['text']}, bg={css['bg']}, success={css['success']}, border={css['border']}
- getPos() MUST apply scale: `const scaleX=680/r.width; const scaleY=420/r.height;`
- Mirror touch events: touchstart→mousedown, touchmove→mousemove, touchend→mouseup
- Animation loop safety: check `if (!ct.querySelector('#sim-canvas'))` before each rAF frame
- Any queried DOM element must be stored in a variable and null-checked before addEventListener; never chain addEventListener directly from querySelector/getElementById

Output complete, improved registerMinigame('{sim_name}', function(ct, data) {{ ... }}); code."""

    return system, user


def sim_visual_objects_prompt(
    chunk_info: dict,
    theme: str = DEFAULT_THEME,
) -> tuple[str, str]:
    """Generate canvas drawing helper functions for key concept objects.

    These functions are injected into the simulation so it draws recognizable
    visual metaphors instead of plain colored rectangles.
    """
    theme_data = get_theme(theme)
    css = theme_data["css"]

    system = (
        "You are a pixel art canvas programmer. Generate compact JavaScript helper functions "
        "that draw recognizable visual objects on a 2D canvas context. "
        "Each function: draw[Name](ctx, x, y, size, color?) using fillRect/arc/bezierCurveTo. "
        "Functions must be self-contained, 5-15 lines each, no external dependencies. "
        "Output ONLY valid JavaScript function declarations. No markdown. No explanation."
    )

    title = chunk_info.get('title', '')
    content = chunk_info.get('content', '')[:400]
    hint = chunk_info.get('simulationHint', '')

    user = f"""Generate 4-6 canvas drawing helper functions for the following educational concept.

## Concept
Title: {title}
Content: {content}
Interaction: {hint}

## Requirements
- Extract the KEY OBJECTS from the concept (e.g. for neuroscience: neuron, brain region, synapse)
- Each function: `function draw[Name](ctx, x, y, size, color) {{ ... }}`
- Use canvas 2D API: ctx.fillRect, ctx.arc, ctx.beginPath, ctx.bezierCurveTo, ctx.fillStyle
- Colors: use parameter `color` or these defaults — accent={css['accent']}, bg={css['bg']}, text={css['text']}
- Size: designed to look good at size=30-60px
- Must be visually recognizable — draw the actual shape, not a rectangle with text
- 5-15 lines per function

Example format:
```javascript
function drawNeuron(ctx, x, y, size, color) {{
  color = color || '{css['accent']}';
  ctx.fillStyle = color;
  ctx.beginPath(); ctx.arc(x, y, size/2, 0, Math.PI*2); ctx.fill();
  // axon
  ctx.strokeStyle = color; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(x+size/2, y); ctx.lineTo(x+size*1.5, y); ctx.stroke();
}}
```

Output ONLY the function declarations (no registerMinigame wrapper)."""

    return system, user


def pixel_art_review_prompt(
    js_code: str,
    code_type: str,
    requirements: str,
    theme: str = DEFAULT_THEME,
) -> tuple[str, str]:
    """AI reviewer for pixel art JS: checks structure and detail, returns improved version.

    Args:
        js_code: The generated pixel art JavaScript code.
        code_type: 'icons' | 'chars' | 'backgrounds' | 'cover'
        requirements: Brief description of what this code should contain.
        theme: Current theme name.
    """
    review_budgets = {
        "icons":       _budget(300, 18_000, "8-12 commands per icon; no comments."),
        "chars":       _budget(450, 28_000, "18-25 per sprite, 15-22 per portrait; no comments."),
        "backgrounds": _budget(550, 36_000, "35-45 per background, 18-25 for drawTitleLogo; no comments."),
        "cover":       _budget(280, 22_000, "50-80 commands; no comments."),
    }
    system = (
        "You are a pixel art code review expert who finds and improves quality issues in pixel art JavaScript. "
        "Your task: review the code and return an improved version if needed, or the original if it is already good. "
        " " + _PIXEL_ART_CONCISE + " "
        "Output must be plain JavaScript only; no markdown or prose. "
        " " + review_budgets.get(code_type, _budget(500, 32_000))
    )

    theme_data = get_theme(theme)
    palette_str = ", ".join(theme_data["pixel_palette"])
    art_rules = _art_direction_rules(theme, "Preserve the same story world, but improve balance, color variety, and scene-to-scene coherence.")

    type_checks = {
        "icons": """
**ICONS check**:
- [ ] Does `window.ICONS = {...}` exist?
- [ ] Is each icon signature `function(g, w, h)`?
- [ ] Does each icon have 8-12 draw commands (gpx/grect)? Add detail if too few, trim if too many
- [ ] Any icon empty or a 1-2 command stub? Complete them""",

        "chars": """
**CHAR_DRAW_FNS and PORTRAITS check**:
- [ ] Does `window.CHAR_DRAW_FNS = {...}` exist with mentor, pet, player?
- [ ] Does `window.PORTRAITS = {...}` exist with mentor, pet, player?
- [ ] Is each CHAR_DRAW_FNS signature `function(g)` (no w/h)?
- [ ] Is each PORTRAITS signature `function(g, w, h)`?
- [ ] Does each sprite have 18-25 draw commands? Add or trim as needed
- [ ] Are the three characters visually distinct (not copy-paste mirrors)?""",

        "backgrounds": """
**BACKGROUNDS and drawTitleLogo check**:
- [ ] Does `window.BACKGROUNDS = [...]` exist with 4 functions?
- [ ] Does `function drawTitleLogo(g, w, h)` exist?
- [ ] Are background functions parameterless (global `px` and `rect`, not gpx/grect)?
- [ ] Does each background have 35-45 draw commands? Add or trim as needed
- [ ] At least 5 horizontal rects for sky gradient?
- [ ] Stars (6+ px points)?
- [ ] Are the 4 backgrounds clearly different scenes?""",

        "cover": """
**drawCover check**:
- [ ] Does `function drawCover(g, w, h)` exist?
- [ ] 50-80 draw commands (gpx/grect)? Keep concise
- [ ] Sky gradient (5+ horizontal rects)?
- [ ] Stars (8+ gpx points)?
- [ ] Foreground character silhouettes or main scene subject?
- [ ] Clear layers (sky → midground → foreground)?""",
    }

    checks = type_checks.get(code_type, "Check that code structure is complete")

    user = f"""Review the following pixel art JavaScript and return improved full code if needed.

## Code type
{requirements}

## Palette (prefer these colors)
{palette_str}

## Art direction
{art_rules}

## Code to review
```javascript
{js_code[:6000]}{'...[truncated]' if len(js_code) > 6000 else ''}
```

## Checklist
{checks}

**General draw rules**:
- Use `gpx(g, x, y, c)` for single pixel, `grect(g, x, y, w, h, c)` for rectangle
- Background functions use global `px(x,y,c)` and `rect(x,y,w,h,c)` (no g)
- Colors must be valid hex strings (e.g. '#ff6a9a')

## Output
If you find issues (empty functions, missing structure, too few or redundant commands), output the fixed full code.
If the code is already good and concise, return it as-is. Prefer concise, clean code.

Output plain JavaScript only; no markdown."""

    return system, user


def pixel_art_review_batch_prompt(
    pieces: dict,   # {code_type: (js_code, requirements)}
    theme: str = DEFAULT_THEME,
) -> tuple[str, str]:
    """Single-call batch review for all pixel art pieces that need improvement.

    Sends only the pieces flagged by the quality heuristic. The LLM returns
    each section wrapped in unique delimiters so they can be parsed back out.
    """
    theme_data = get_theme(theme)
    palette_str = ", ".join(theme_data["pixel_palette"])
    art_rules = _art_direction_rules(theme, "Keep the same world language across every section while improving color balance and visual diversity.")

    type_checks = {
        "icons": (
            "- `window.ICONS = {...}` exists; each signature is `function(g, w, h)`\n"
            "- Each icon has 8-12 draw commands (gpx/grect); stub icons must be completed\n"
            "- Use `gpx(g,x,y,c)` and `grect(g,x,y,w,h,c)`"
        ),
        "chars": (
            "- `window.CHAR_DRAW_FNS = {...}` with mentor, pet, player; signature `function(g)` (no w/h)\n"
            "- `window.PORTRAITS = {...}` with mentor, pet, player; signature `function(g, w, h)`\n"
            "- Each sprite 18-25 draw commands; 3 characters visually distinct"
        ),
        "backgrounds": (
            "- `window.BACKGROUNDS = [...]` with 4 parameterless functions\n"
            "- `function drawTitleLogo(g, w, h)` exists\n"
            "- Background functions use global `px(x,y,c)` / `rect(x,y,w,h,c)` (no g arg)\n"
            "- Each background 35-45 draw commands; sky gradient (5+ rects); stars (6+ px); 4 distinct scenes"
        ),
        "cover": (
            "- `function drawCover(g, w, h)` exists\n"
            "- 50-80 draw commands (gpx/grect)\n"
            "- Sky gradient (5+ rects), stars (8+ gpx), foreground subjects; clear layers"
        ),
    }

    draw_rules = (
        "Draw rules: `gpx(g,x,y,c)` single pixel | `grect(g,x,y,w,h,c)` rect | "
        "background fns use global `px`/`rect` (no g). Colors must be valid hex."
    )

    sections = []
    for code_type, (js_code, requirements) in pieces.items():
        tag = code_type.upper()
        checks = type_checks.get(code_type, "Check structure is complete")
        truncated = js_code[:5500] + ("\n// ...[truncated]" if len(js_code) > 5500 else "")
        sections.append(
            f"## {tag} — {requirements}\n"
            f"Checklist:\n{checks}\n\n"
            f"// =={tag}_START==\n{truncated}\n// =={tag}_END=="
        )

    system = (
        "You are a pixel art JavaScript code reviewer. For each section, check the checklist. "
        "Return the fixed full code if issues are found, or the original if it is already good. "
        "Output ONLY JavaScript wrapped in the exact delimiters shown — no markdown, no prose, no extra text."
    )

    user = f"""Review each pixel art section below. Use palette: {palette_str}
{draw_rules}

Art direction:
{art_rules}

{chr(10).join(sections)}

Return ALL sections using EXACTLY these delimiters (even if unchanged):

// ==ICONS_START==
[icons code]
// ==ICONS_END==

// ==CHARS_START==
[chars code]
// ==CHARS_END==

// ==BACKGROUNDS_START==
[backgrounds code]
// ==BACKGROUNDS_END==

// ==COVER_START==
[cover code]
// ==COVER_END==

Only include sections you received above. Output JavaScript only — no markdown."""

    return system, user
