# Creating a Git Tag from Terminal

## Step-by-Step Instructions

```bash
# 1. Make sure you're on the correct branch (main or master)
git checkout main

# 2. Create the tag (example: v1.0.0)
git tag v1.0.0

# 3. Push the tag to GitHub
git push origin v1.0.0
```

## What Each Command Does

### **Step 1: `git checkout main`**
- **Purpose**: Switches to your main branch (or master, depending on your repo)
- **Why**: You want to tag a stable version of your code, typically from your main branch
- **Note**: If your default branch is named `master`, use `git checkout master` instead

### **Step 2: `git tag v1.0.0`**
- **Purpose**: Creates a **lightweight tag** locally on your computer
- **What it does**: Marks the current commit with a version label (v1.0.0)
- **Tag naming**: The `v*` pattern matches your GitHub Action trigger (`tags: - 'v*'`)
- **Convention**: Follow [Semantic Versioning](https://semver.org/):
  - `v1.0.0` - Major.Minor.Patch
  - `v1.0.1` - Bug fixes
  - `v1.1.0` - New features
  - `v2.0.0` - Breaking changes

### **Step 3: `git push origin v1.0.0`**
- **Purpose**: Uploads the tag to GitHub
- **What happens next**:
  1. GitHub receives the tag
  2. Your GitHub Action automatically triggers
  3. The workflow builds your assets
  4. Creates a new **Release** on GitHub
  5. Uploads `.AppImage` and `.zip` files to that release



## Alternative: Annotated Tags (Best Practice for Releases)

For production releases, use **annotated tags** with messages:

```bash
# Create an annotated tag with a message
git tag -a v1.0.0 -m "Release version 1.0.0 - Initial stable release"

# Push to GitHub
git push origin v1.0.0
```

**Benefits:**
- Contains author name, email, and date
- Includes a release message
- Better for official releases
- Shows up more prominently in `git log`



## Verify Your Tags

### **Check local tags:**
```bash
git tag
# Output: v1.0.0
```

### **Check tags on GitHub:**
```bash
git ls-remote --tags origin
```

### **See tag details:**
```bash
git show v1.0.0
```



## Delete a Tag (If You Made a Mistake)

### **Delete locally:**
```bash
git tag -d v1.0.0
```

### **Delete from GitHub:**
```bash
git push origin :refs/tags/v1.0.0
# or
git push origin --delete v1.0.0
```



## Common Tag Versioning Examples

```bash
# First release
git tag v1.0.0

# Bug fix
git tag v1.0.1

# New feature (backward compatible)
git tag v1.1.0

# Breaking changes
git tag v2.0.0

# Pre-release versions
git tag v1.0.0-beta.1
git tag v1.0.0-rc.1
```

## ⚠️ Troubleshooting

### **Problem: "Tag already exists"**
```bash
# Solution: Use a different version number
git tag v1.0.1
```

### **Problem: "Permission denied"**
- Make sure you have push access to the repository
- Check if branch protection rules allow tag creation

### **Problem: "GitHub Action didn't trigger"**
- Verify the tag starts with `v` (e.g., `v1.0.0` not `1.0.0`)
- Check your workflow file has: `tags: - 'v*'`
- Wait 10-30 seconds, then check the **Actions** tab on GitHub



## Complete Workflow Example

```bash
# 1. Make your final changes
git add .
git commit -m "Prepare for v1.0.0 release"

# 2. Push changes
git push origin main

# 3. Create and push tag
git tag -a v1.0.0 -m "Release v1.0.0 - Production ready"
git push origin v1.0.0

# 4. Watch the magic happen! 🎉
# Go to: https://github.com/YOUR_USERNAME/YOUR_REPO/actions
```



## What Happens After Pushing the Tag

1. **GitHub receives the tag** → Triggers your workflow
2. **Action runs** → Builds AppImage and Zip files
3. **Release created** → Automatically on GitHub
4. **Files uploaded** → Available for download
5. **Users can download** → From the Releases page

**Check your release at:**
```
https://github.com/YOUR_USERNAME/YOUR_REPO/releases/tag/v1.0.0
```

That's it!
