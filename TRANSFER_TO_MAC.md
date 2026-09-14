# Transfer Code to Mac System

## 🎯 Transfer Details

**From**: Current Linux system
**To**: Mac system (IP: 192.168.56.88)
**Destination**: `/Users/mac/Desktop/ashish_kumar/Mtech/code/ocr_hindi_main`
**Exclude**: venv, dataset

---

## ✅ Recommended Method: Using rsync

### Command:

```bash
rsync -avz --progress \
  --exclude='venv' \
  --exclude='dataset' \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='*.pt' \
  --exclude='*.pth' \
  /home/work/work/code/model_train/ \
  mac@192.168.56.88:/Users/mac/Desktop/ashish_kumar/Mtech/code/ocr_hindi_main/
```

### Explanation:
- `-a`: Archive mode (preserves permissions, timestamps)
- `-v`: Verbose (shows files being transferred)
- `-z`: Compress during transfer (faster)
- `--progress`: Shows progress bar
- `--exclude`: Excludes specified folders/files

---

## 📦 What Will Be Transferred:

✅ **Included**:
- All Python scripts (*.py)
- Configuration files (*.yaml, *.json)
- Checkpoints (if you want them, remove --exclude='*.pt')
- Results files
- Papers (our_paper folder)
- Documentation (*.md)
- Logs
- Notebooks

❌ **Excluded**:
- venv/ (virtual environment)
- dataset/ (data files)
- *.pyc (compiled Python)
- __pycache__/ (Python cache)
- .git/ (git repository - optional)
- *.pt, *.pth (model checkpoints - optional)

---

## 🚀 Step-by-Step Transfer

### Step 1: Test Connection First

```bash
# Test SSH connection to Mac
ssh mac@192.168.56.88
```

If successful, you should be able to login. Then exit:
```bash
exit
```

### Step 2: Create Destination Directory on Mac (if needed)

```bash
ssh mac@192.168.56.88 "mkdir -p /Users/mac/Desktop/ashish_kumar/Mtech/code/ocr_hindi_main"
```

### Step 3: Transfer Files

```bash
# Full transfer command
rsync -avz --progress \
  --exclude='venv' \
  --exclude='dataset' \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  /home/work/work/code/model_train/ \
  mac@192.168.56.88:/Users/mac/Desktop/ashish_kumar/Mtech/code/ocr_hindi_main/
```

---

## 🔄 Alternative Method: Using scp

If rsync is not available:

```bash
# First, create a tarball excluding unwanted directories
cd /home/work/work/code
tar -czf model_train_transfer.tar.gz \
  --exclude='model_train/venv' \
  --exclude='model_train/dataset' \
  --exclude='model_train/*.pyc' \
  --exclude='model_train/__pycache__' \
  model_train/

# Transfer the tarball
scp model_train_transfer.tar.gz mac@192.168.56.88:/Users/mac/Desktop/ashish_kumar/Mtech/code/

# Then SSH to Mac and extract
ssh mac@192.168.56.88
cd /Users/mac/Desktop/ashish_kumar/Mtech/code/
tar -xzf model_train_transfer.tar.gz -C ocr_hindi_main/
rm model_train_transfer.tar.gz
exit
```

---

## 📊 Estimated Transfer Size

Without venv and dataset:

```bash
# Check size before transfer
du -sh /home/work/work/code/model_train \
  --exclude=venv \
  --exclude=dataset
```

Estimated: ~500 MB - 2 GB (depends on checkpoints and logs)

---

## ⚡ Quick Transfer (If You Want Checkpoints)

### Option 1: Include Checkpoints

```bash
rsync -avz --progress \
  --exclude='venv' \
  --exclude='dataset' \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  /home/work/work/code/model_train/ \
  mac@192.168.56.88:/Users/mac/Desktop/ashish_kumar/Mtech/code/ocr_hindi_main/
```

### Option 2: Exclude Checkpoints (Faster)

```bash
rsync -avz --progress \
  --exclude='venv' \
  --exclude='dataset' \
  --exclude='checkpoints' \
  --exclude='*.pt' \
  --exclude='*.pth' \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  /home/work/work/code/model_train/ \
  mac@192.168.56.88:/Users/mac/Desktop/ashish_kumar/Mtech/code/ocr_hindi_main/
```

---

## 🔧 After Transfer - Setup on Mac

Once transferred, SSH to Mac and setup:

```bash
# SSH to Mac
ssh mac@192.168.56.88

# Navigate to directory
cd /Users/mac/Desktop/ashish_kumar/Mtech/code/ocr_hindi_main

# Create new virtual environment on Mac
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import torch; print(torch.__version__)"
```

---

## 📝 Troubleshooting

### Issue 1: Permission Denied

```bash
# Check if you can SSH
ssh mac@192.168.56.88

# If password is required, it will prompt
# If SSH key needed, set it up first
```

### Issue 2: Destination Directory Not Found

```bash
# Create the full path on Mac
ssh mac@192.168.56.88 "mkdir -p /Users/mac/Desktop/ashish_kumar/Mtech/code/ocr_hindi_main"
```

### Issue 3: rsync Not Found

Use the tar + scp method described above.

### Issue 4: Transfer is Slow

Add compression and reduce verbosity:

```bash
rsync -az --progress \
  --exclude='venv' \
  --exclude='dataset' \
  /home/work/work/code/model_train/ \
  mac@192.168.56.88:/Users/mac/Desktop/ashish_kumar/Mtech/code/ocr_hindi_main/
```

---

## ✅ Quick Check After Transfer

On Mac, verify the transfer:

```bash
ssh mac@192.168.56.88

cd /Users/mac/Desktop/ashish_kumar/Mtech/code/ocr_hindi_main

# Check structure
ls -la

# Should see:
# - configs/
# - scripts/
# - our_paper/
# - results/
# - checkpoints/ (if included)
# - requirements.txt
# - etc.

# Verify no venv or dataset
ls -la | grep venv     # Should be empty
ls -la | grep dataset  # Should be empty
```

---

## 🎯 One-Line Command (Copy-Paste Ready)

```bash
rsync -avz --progress --exclude='venv' --exclude='dataset' --exclude='*.pyc' --exclude='__pycache__' /home/work/work/code/model_train/ mac@192.168.56.88:/Users/mac/Desktop/ashish_kumar/Mtech/code/ocr_hindi_main/
```

---

## 📦 What Gets Transferred (Summary)

```
model_train/
├── configs/              ✅ (all YAML configs)
├── scripts/              ✅ (all Python scripts)
├── our_paper/            ✅ (all papers and docs)
├── results/              ✅ (evaluation results)
├── checkpoints/          ✅ (model checkpoints)
├── logs/                 ✅ (training logs)
├── papers/               ✅ (reference papers)
├── target/               ✅ (documentation)
├── requirements.txt      ✅
├── *.py                  ✅
├── *.md                  ✅
├── venv/                 ❌ EXCLUDED
└── dataset/              ❌ EXCLUDED
```

---

## 💡 Pro Tips

1. **Test First**: Test with a small directory first to verify connection
2. **Use Screen**: For large transfers, use `screen` or `tmux` to avoid interruption
3. **Resume**: rsync can resume interrupted transfers, just run the same command again
4. **Bandwidth**: Use `-z` for compression on slow networks
5. **Dry Run**: Add `--dry-run` to see what will be transferred without actually transferring

---

*Ready to transfer? Just copy the one-line command above!* 🚀
