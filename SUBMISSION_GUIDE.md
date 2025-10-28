# 📤 Submission Guide - Step by Step

## Overview
Submit your solution via Pull Request to demonstrate version control skills and enable easy code review.

---

## 🔄 Submission Process

### Step 1: Fork the Repository

1. Go to: `https://github.com/COMPANY/research-paper-rag-assessment`
2. Click the **"Fork"** button (top-right)
3. Select your personal account
4. Wait for fork to complete

### Step 2: Clone Your Fork

```bash
# Clone your forked repository
git clone <github_repo_link>

```

### Step 3: Create Working Branch

```bash
# Create a new branch with your name
git checkout -b submission/firstname-lastname

# Example:
git checkout -b submission/john-doe

# Verify you're on the right branch
git branch
# Should show: * submission/john-doe
```

### Step 4: Build Your Solution

Create your project structure:

```bash
# Create directories
mkdir -p src/models src/services src/api tests

# Start coding!
```

**Keep Original Files**:
- Don't delete `sample_papers/` directory
- Don't modify `test_queries.json`
- Don't change `EVALUATION_CRITERIA.md`

### Step 5: Commit Your Work

```bash
# Add all your files
git add .

# Check what's staged
git status

# Commit with clear message
git commit -m "feat: implement RAG system for research papers

- Add PDF processing with PyPDF2
- Implement Qdrant vector storage
- Create FastAPI endpoints
- Add query pipeline with Ollama
- Include documentation and tests"

# Push to your fork
git push origin submission/firstname-lastname
```

**Commit Message Best Practices**:
- Use present tense: "Add feature" not "Added feature"
- Be descriptive but concise
- Group related changes

### Step 6: Create Pull Request

1. **Go to GitHub** → Your fork
2. You'll see: *"submission/firstname-lastname had recent pushes"*
3. Click **"Compare & pull request"**

4. **Configure PR**:
   - **Base repository**: `COMPANY/research-paper-rag-assessment`
   - **Base branch**: `main`
   - **Head repository**: `YOUR_USERNAME/research-paper-rag-assessment`
   - **Compare branch**: `submission/firstname-lastname`

5. **Fill out PR template** ([PULL_REQUEST_TEMPLATE.md](PULL_REQUEST_TEMPLATE.md))

6. Click **"Create pull request"**