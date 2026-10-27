# Connecting Instagram to mogdhopaul.com

Do this once. After that, new Instagram photos appear on the site every night by themselves.
It takes about 15 minutes. You never need to paste a token into a chat or a file in the repo.

## 1. Make your Instagram a Creator account

1. In the Instagram app: **Profile → ☰ menu → Settings and privacy → Account type and tools → Switch to professional account**.
2. Choose **Creator**. Pick any category (for example "Photographer" or "Blogger"). Your account stays the same for followers.

## 2. Create a Meta app

1. Go to <https://developers.facebook.com/> and log in with your Facebook account. Accept the developer terms if asked.
2. **My Apps → Create app**. Name it something like "mogdhopaul site". When asked for a use case, pick **Other**, then app type **Business**.
3. In the app dashboard, find **Instagram** and click **Set up**. Choose **API setup with Instagram login**. (No Facebook page is needed for this one.)

## 3. Get a long-lived token

1. In **API setup with Instagram login**, go to **Generate access tokens → Add account**, and log in as @mogdhopaul.
2. Click **Generate token** next to your account. Copy the token. It lasts 60 days; the site renews it every month for you.

## 4. Add the token to GitHub

1. Open <https://github.com/mogdho/mogdhopaul> → **Settings → Secrets and variables → Actions → New repository secret**.
2. Name: `IG_TOKEN`. Value: the token. Save.

## 5. Let GitHub renew the token by itself

1. Go to <https://github.com/settings/personal-access-tokens/new> (fine-grained token).
2. Name: "renew instagram token". Expiration: the longest allowed. Repository access: **Only select repositories → mogdhopaul**.
3. Permissions → Repository permissions → **Secrets: Read and write**. Generate, copy.
4. Add it as another repository secret named `GH_PAT`.
5. When this GitHub token expires, GitHub emails you; make a new one the same way.

## 6. Run it once

1. In the repo, open **Actions → Update photos → Run workflow**.
2. After a minute, your photos are on <https://mogdhopaul.com/photos/>.

## Hiding a photo

Add the post's link (for example `https://www.instagram.com/p/ABC123/`) on its own line in
`data/photos-exclude.txt`. It disappears on the next nightly run.

## Captions

Only the place and date are shown. Put the place on the first line of your caption, or after a 📍,
for example `📍 Paris, France`. Hashtags and other text are ignored.

## If something breaks

If Instagram stops answering (for example the token expired), the nightly job fails, GitHub emails you,
and the site keeps the photos it already has. Generate a new token (step 3) and update `IG_TOKEN`.
