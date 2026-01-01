# Ezrat Nashim Database - Project Instructions

**Note:** This is a **dynamic document** that describes the **current state** of the repository. As Claude Code, you should **proactively update this file** when you:
- Discover new information about how the codebase works
- Learn about architectural decisions made during our work
- Reach important conclusions during discussions
- Find other significant details about the project

Focus on documenting how things work **NOW**, not historical changes (that's what git history is for). Keep it concise and useful for understanding the codebase in future sessions.

---

## What This Is
Crowdsourced database tracking women's seating in synagogues worldwide. Two metrics:
1. Size of ezrat nashim relative to men's section (L/M/S/X/&)
2. Visibility/audibility quality (1-5 star rating)

Goal: Simple, observable data that correlates with women's broader experience in the synagogue.

**Philosophy**: Rather than attempting comprehensive evaluations, we intentionally limit ourselves to a small set of measurable indicators in order to keep the site easy to use and contribute to.

## Tech Stack
- **Backend**: Django
- **Frontend**: Bootstrap 5.3
- **Database**: PostgreSQL
- **Hosting**: Fly.io
- **Maps**: Leaflet
- **Package Management**: Poetry
- **Testing**: Run tests with `poetry run ptw -- -- --testmon --disable-warnings /app/app/tests/`
- **Commits**: Use [conventional commits](https://www.conventionalcommits.org/) (e.g., `fix:`, `feat:`, `refactor:`)

## Code Quality & Testing Philosophy

### Testing
- **TDD approach**: Prefer using Test-Driven Development when it makes sense - write tests first to drive design and implementation
- **Tool**: pytest with pytest-describe for test organization
- **Quality over quantity**: Aggressively remove redundant tests - each test should verify unique behavior
- **Naming**: Test names must accurately describe what they test, not what you wish they tested
- **Simplicity**: Prefer inline setup over fixtures unless the abstraction adds clear value
- **Review stance**: When reviewing code, be critical and suggest improvements - "looks fine" isn't helpful

### Code Review Approach
- When asked "what do you think?", provide honest critique and concrete suggestions
- Proactively identify redundancy, misleading names, and unnecessary complexity
- Suggest removals, not just additions

## Core Design Decisions

### Data Model
- Multi-room support (main sanctuary, chapel, etc.)
- Coordinate-based location storage
- Anyone can edit (Wikipedia model - no formal review)
- Letter codes: L (equal/larger), M (half size), S (less than half), X (no women's section), & (mixed seating)

### Geographic Privacy
- Public map: approximate location (~1km radius)
- Exact address: available via "Open in Maps" and edit page
- Duplicate prevention: coordinate-based matching

### Site Structure
- Homepage = map (not explanation page)
- Navigation: Browse Shuls | Add a Shul | About | Contact
- Map-first because tool is self-explanatory

## Key Policies

### Content Philosophy
- Document observable facts about public spaces
- Synagogues can't request removal just because they dislike being documented
- Security-based delisting considered case-by-case (not yet implemented)
- Accept imperfect data over no data

### Privacy & Security
- Address hiding for security requests (design in progress)
- Full delisting only for extreme cases
- Corrections always welcome for inaccurate data

## Known Trade-offs
- **Subjectivity**: Visibility/audibility ratings vary by person
- **No verification**: Trusting crowdsourced data
- **Limited scope**: Only tracking two metrics, not comprehensive evaluation
- **Simplicity over precision**: Intentional choice to keep it usable
