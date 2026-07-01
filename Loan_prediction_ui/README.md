# Deploying the Stock Prediction App on Vercel (Free)

## Folder structure (must match exactly)
```
stock_app_vercel/
├── api/
│   ├── index.py                  <- FastAPI backend (all routes under /api/...)
│   ├── preprocessor.pkl
│   └── stock_prediction_model.pkl   <- 131MB, needs Git LFS (see Step 2)
├── data/
│   └── stock_data_messy.csv
├── index.html                    <- frontend, served at "/"
├── vercel.json                   <- tells Vercel how to route requests
├── requirements.txt              <- Python dependencies
├── .gitattributes                <- tells Git to use LFS for the big .pkl file
└── .gitignore
```

---

## Step 1: Install Git LFS (one-time setup on your computer)

Your model file (`stock_prediction_model.pkl`) is 131MB. GitHub blocks any
single file over 100MB on a normal push, so we need **Git LFS** (Large File
Storage) to handle it.

1. Download and install Git LFS: https://git-lfs.com
2. Open a terminal inside your project folder and run:
   ```
   git lfs install
   ```

---

## Step 2: Create a Git repo and push to GitHub

```bash
cd stock_app_vercel
git init
git lfs track "api/stock_prediction_model.pkl"
git add .gitattributes
git add .
git commit -m "Initial commit - stock prediction app"
```

Now create a new (empty) repository on GitHub (no README, no .gitignore —
just an empty repo), then:

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

If Git LFS is set up correctly, you'll see the big .pkl file uploading
separately from the rest ("Uploading LFS objects...").

---

## Step 3: Deploy on Vercel

1. Go to https://vercel.com and sign up / log in (you can use your GitHub
   account to sign in - this also makes Step 4 automatic).
2. Click **"Add New..." → "Project"**.
3. Select **"Import Git Repository"** and choose the GitHub repo you just
   pushed.
4. Vercel will auto-detect it as a Python project (because of
   `requirements.txt` and the `api/` folder). You usually don't need to
   change any build settings.
5. Click **Deploy**.
6. Wait 1-3 minutes for the build to finish (it's installing pandas,
   scikit-learn, etc., and bundling your model file — this can take a
   little longer than a normal site).
7. Once done, Vercel gives you a live URL like:
   ```
   https://your-project-name.vercel.app
   ```
8. Open that URL — your stock prediction app should load.

---

## Step 4: Automatic redeploys (bonus)

Since your project is connected to GitHub, any time you run:
```bash
git add .
git commit -m "some change"
git push
```
Vercel automatically rebuilds and redeploys your app within a minute or
two — no manual redeploy needed.

---

## Common errors and fixes

**"File size exceeds limit" during git push**
→ Git LFS isn't tracking the file properly. Run `git lfs track "api/stock_prediction_model.pkl"`
again, then `git add .gitattributes`, commit, and push again.

**Build fails with "Serverless Function exceeded maximum size"**
→ This means the model + dependencies together are too big (Vercel's limit
for Python functions is 500MB uncompressed). If this happens, the model
needs to be hosted externally (e.g. Hugging Face Hub) and downloaded inside
the function instead of bundled directly — let me know if you hit this and
I'll set that up.

**App loads but predictions fail / 500 error**
→ Open the **Vercel dashboard → your project → Deployments → (latest) →
Functions tab** to see the real Python error in the logs.

**Page loads with no styling / dropdown empty**
→ Open the browser console (F12) and check for a red error on `/api/companies`
— if you see a 404, double check `vercel.json` is in the project ROOT folder,
not inside `api/`.
