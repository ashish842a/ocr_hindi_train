# Model Changelog Usage Guide

This guide explains how to maintain and use the model version tracking system.

## 📁 Files Overview

- **MODEL_CHANGELOG.md** - Markdown version (GitHub-friendly, easy to edit)
- **MODEL_CHANGELOG.html** - HTML version (beautiful presentation, copy buttons)
- **scripts/update_changelog.py** - Helper script to update changelogs

## 🚀 Quick Start

### After Completing a Training Run

1. **Get your results** (CER and WER from evaluation)
2. **Update the changelog automatically**:

   ```bash
   # Option 1: Manual values
   python scripts/update_changelog.py --version v2 --cer 12.5 --wer 26.3

   # Option 2: From results JSON
   python scripts/update_changelog.py --version v2 --results-json results/a1_test.json
   ```

3. **Review the updated changelog**:
   ```bash
   cat MODEL_CHANGELOG.md | grep "v2"
   ```

4. **Open the HTML version** in your browser:
   ```bash
   # Linux
   xdg-open MODEL_CHANGELOG.html

   # Mac
   open MODEL_CHANGELOG.html

   # Windows
   start MODEL_CHANGELOG.html
   ```

## 📝 Manual Updates

### Updating Markdown (MODEL_CHANGELOG.md)

1. Open `MODEL_CHANGELOG.md` in your editor
2. Find the version section (e.g., `## Version 2`)
3. Replace `TBD` with actual values
4. Update status badges:
   - `📝 Planned` → `🔄 Current` → `✅ Complete` or `❌ Failed`
5. Add any observations or notes

### Updating HTML (MODEL_CHANGELOG.html)

1. Open `MODEL_CHANGELOG.html` in your editor
2. Find the version section in HTML
3. Update the table rows and version sections
4. Update status badges:
   ```html
   <span class="status-badge status-planned">Planned</span>
   → <span class="status-badge status-complete">Complete</span>
   ```

## 🔄 Complete Workflow Example

### Running and Documenting v2

```bash
# 1. Prepare data
python3 scripts/prepare_data_simple.py \
    --data-root dataset \
    --output-dir data_processed \
    --min-char-freq 1 \
    --normalize

# 2. Train
./scripts/train_with_log.sh configs/a1_baseline.yaml

# 3. Evaluate
./scripts/evaluate_with_log.sh \
    --config configs/a1_baseline.yaml \
    --checkpoint checkpoints/a1_baseline/best.pt \
    --split test \
    --output results/a1_test.json

# 4. Update changelog
python scripts/update_changelog.py --version v2 --results-json results/a1_test.json

# 5. Archive
./experiments/archive_experiment.sh v2_charset100 "Baseline with 100 chars - CER 12.5%"

# 6. Review changelog
cat MODEL_CHANGELOG.md | grep -A 20 "Version 2"
xdg-open MODEL_CHANGELOG.html
```

## 📊 Adding New Versions

### Template in Markdown

Add this template to `MODEL_CHANGELOG.md`:

```markdown
## Version X: [Name] [Status Emoji]

### 📅 Metadata
- **Version**: vX_name
- **Date**: YYYY-MM-DD
- **Status**: [Planned/In Progress/Complete/Failed]
- **Archive**: path or TBD

### 🏗️ Model Architecture
[Describe architecture or changes]

### ⚙️ Configuration Changes from vN
**🔴 Changed**:
- parameter: old → new

**🟢 Unchanged**:
- [List what stayed same]

### 📊 Results
Training:
  - Train Loss: X.XXX
  - Val Loss: X.XXX

Test Evaluation:
  - CER: XX.XX% [XX.XX%, XX.XX%]
  - WER: XX.XX% [XX.XX%, XX.XX%]

### 🔄 How to Run
\`\`\`bash
# Complete reproduction commands
\`\`\`
```

### Template in HTML

Add a new section in `MODEL_CHANGELOG.html`:

```html
<div class="version-section" id="vX">
    <h2>Version X: [Name] [Emoji]</h2>

    <div class="metadata">
        <div class="metadata-item">
            <span class="metadata-label">Version</span>
            vX_name
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Status</span>
            <span class="status-badge status-planned">Planned</span>
        </div>
    </div>

    <!-- Add sections as needed -->
</div>
```

## 📈 Viewing Comparisons

### Compare Two Versions

```bash
# View differences
diff <(grep -A 30 "Version 1" MODEL_CHANGELOG.md) \
     <(grep -A 30 "Version 2" MODEL_CHANGELOG.md)

# Extract just the results
grep -A 5 "Test Evaluation:" MODEL_CHANGELOG.md
```

### Generate Comparison Table

```bash
# Extract key metrics
echo "Version | CER | WER"
echo "--------|-----|----"
grep "| \*\*v" MODEL_CHANGELOG.md | sed 's/|/,/g' | \
    awk -F',' '{print $2 " | " $6 " | " $7}'
```

## 🎨 HTML Features

The HTML version includes:

- **📑 Table of Contents** - Quick navigation
- **🎨 Syntax Highlighting** - Color-coded code blocks
- **📋 Copy Buttons** - One-click command copying
- **🏷️ Status Badges** - Visual status indicators
- **📊 Tables** - Formatted comparison tables
- **🔍 Smooth Scrolling** - Better navigation

### Using Copy Buttons

1. Open `MODEL_CHANGELOG.html` in browser
2. Find the command you want to run
3. Click "Copy" button in top-right of code block
4. Paste into terminal

## 📚 For Paper Writing

### Export for LaTeX

```bash
# Extract comparison table
grep -A 10 "## 📊 Results Comparison" MODEL_CHANGELOG.md > paper_table.md

# Convert to LaTeX (using pandoc if installed)
pandoc paper_table.md -o paper_table.tex
```

### Export Specific Version

```bash
# Extract version 2 section
sed -n '/^## Version 2/,/^## Version 3/p' MODEL_CHANGELOG.md > v2_details.md

# Or use grep
grep -A 50 "^## Version 2" MODEL_CHANGELOG.md > v2_details.md
```

## 🔧 Troubleshooting

### Changelog Not Updating

```bash
# Check file permissions
ls -l MODEL_CHANGELOG.md

# Make sure you're in project root
pwd  # Should show: .../model_train

# Try manual edit
nano MODEL_CHANGELOG.md
```

### HTML Not Displaying Correctly

- Make sure to open in a modern browser (Chrome, Firefox, Edge)
- Check for JavaScript errors (F12 → Console)
- Verify file encoding is UTF-8

### Update Script Not Working

```bash
# Check Python version
python3 --version  # Should be 3.6+

# Run with verbose output
python scripts/update_changelog.py --version v2 --cer 12.5 --wer 26.3 -v
```

## 💡 Best Practices

1. **Update immediately** after evaluation completes
2. **Keep both files in sync** (Markdown and HTML)
3. **Add observations** beyond just numbers
4. **Document failures** as well as successes
5. **Use descriptive version names** (v2_charset100, not just v2)
6. **Include reproduction commands** for every version
7. **Archive before updating** to new version

## 📝 Quick Reference

| Task | Command |
|------|---------|
| Update changelog | `python scripts/update_changelog.py --version v2 --results-json results/a1_test.json` |
| View changelog | `cat MODEL_CHANGELOG.md` or `xdg-open MODEL_CHANGELOG.html` |
| Compare versions | `diff <(grep -A 30 "Version 1" MODEL_CHANGELOG.md) <(grep -A 30 "Version 2" MODEL_CHANGELOG.md)` |
| Extract table | `grep "\| \*\*v" MODEL_CHANGELOG.md` |
| Add new version | Use templates above |

---

**Need Help?** Check the examples in existing version sections!
