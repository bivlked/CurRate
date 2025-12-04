# BUILD Command - Code Implementation

This command implements the planned changes following the implementation plan and creative phase decisions.

## Memory Bank Integration

Reads from:
- `memory-bank/tasks.md` - Implementation plan and checklists
- `memory-bank/creative/creative-*.md` - Design decisions (Level 3-4)
- `memory-bank/activeContext.md` - Current project context

Updates:
- `memory-bank/tasks.md` - Implementation progress and status
- `memory-bank/progress.md` - Build status and observations

## Progressive Rule Loading

### Step 1: Load Core Rules
```
Load: .cursor/rules/isolation_rules/main.mdc
Load: .cursor/rules/isolation_rules/Core/memory-bank-paths.mdc
Load: .cursor/rules/isolation_rules/Core/command-execution.mdc
```

### Step 2: Load BUILD Mode Map
```
Load: .cursor/rules/isolation_rules/visual-maps/implement-mode-map.mdc
```

### Step 3: Load Complexity-Specific Implementation Rules
Based on complexity level from `memory-bank/tasks.md`:

**Level 1:**
```
Load: .cursor/rules/isolation_rules/Level1/workflow-level1.mdc
Load: .cursor/rules/isolation_rules/Level1/optimized-workflow-level1.mdc
```

**Level 2:**
```
Load: .cursor/rules/isolation_rules/Level2/workflow-level2.mdc
```

**Level 3-4:**
```
Load: .cursor/rules/isolation_rules/Level3/implementation-intermediate.mdc
Load: .cursor/rules/isolation_rules/Level4/phased-implementation.mdc
```

## Workflow

1. **Verify Prerequisites**
   - Check `memory-bank/tasks.md` for planning completion
   - For Level 3-4: Verify creative phase documents exist
   - Review implementation plan

2. **Determine Complexity Level**
   - Read complexity level from `memory-bank/tasks.md`
   - Load appropriate workflow rules

3. **Execute Implementation**

   **Level 1 (Quick Bug Fix):**
   - Review bug report
   - Examine relevant code
   - Implement targeted fix
   - Test fix
   - Update `memory-bank/tasks.md`

   **Level 2 (Simple Enhancement):**
   - Review build plan
   - Examine relevant code areas
   - Implement changes sequentially
   - Test changes
   - Update `memory-bank/tasks.md`

   **Level 3-4 (Feature/System):**
   - Review plan and creative decisions
   - Create directory structure
   - Build in planned phases
   - Test each phase
   - Integration testing
   - Document implementation
   - Update `memory-bank/tasks.md` and `memory-bank/progress.md`

4. **Command Execution**
   - Document all commands executed
   - Document results and observations
   - Follow platform-specific command guidelines

5. **Verification**
   - Verify all build steps completed
   - Verify changes meet requirements
   - Update `memory-bank/tasks.md` with completion status

## Usage

Type `/build` to start implementation based on the plan in `memory-bank/tasks.md`.

## Next Steps

After implementation complete, proceed to `/reflect` command for task review.

