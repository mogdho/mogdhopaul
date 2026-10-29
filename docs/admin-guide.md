# Using the admin at mogdhopaul.com/admin

The admin lets you change your photos, projects and text from your phone or computer.
Every save goes live on the site in about two minutes.

## 1. Make your GitHub key (once)

The key is how the admin proves it's you. Make it once, then paste it on each device you use.

1. On GitHub, open **Settings → Developer settings → Personal access tokens → Fine-grained tokens**
   (or go straight to <https://github.com/settings/personal-access-tokens/new>).
2. **Token name:** `mogdhopaul admin`. **Expiration:** the longest it offers.
3. **Repository access:** *Only select repositories* → `mogdho/mogdhopaul`.
4. **Permissions → Repository permissions:**
   - **Contents:** Read and write
   - **Actions:** Read-only
5. Click **Generate token** and copy it. GitHub shows it only once, so keep it somewhere safe
   (a password manager is ideal).

When the key expires, GitHub emails you. Make a new one the same way and log in again.

## 2. Log in

Open <https://mogdhopaul.com/admin/>, paste the key and press **Log in**.
The device remembers you until you press **Log out**.

## 3. Make changes

**Profile photo**
- At the top of **Photos**, press **Change profile photo** and pick a photo. Drag it inside the frame
  to choose what shows, then save. It replaces the photo beside your name on the home page and the
  picture shown when someone shares a link to your site. **Keep the current photo** cancels.

**Photos**
- **Add photos** lets you pick one or several at once (JPG or PNG; iPhone HEIC photos need to be
  saved as JPG first). They are made smaller on your device and their location data is removed,
  so the original never leaves your phone.
- Type the **Place** (in English) and check the **Date**. Leave Place empty to show only the date.
- Photos are shown in a fixed frame, so some of each photo is cut off. **Drag the photo** inside its
  frame to choose which part stays; the small frame shows how it looks on the home page.
  **Centre** puts it back in the middle. The whole photo is uploaded, so you can change this any time.
- The six newest photos appear on the home page; all of them on the Photos page.

**Projects**
- Edit any field, add or delete projects, and move them up or down.
- Tick **Show on home page** for exactly three.
- The short version is used on the home page; leave it empty to use the full description.

**Text & links**
- Your identity line, home intro, video-editing text, About page sections, WhatsApp, email and
  profile links.
- A blank line starts a new paragraph.
- **Skills**: your tech stack and tools, shown on the home page above your projects as round stamps.
  **Add to tech stack / Add to tools** adds one; type its name and a matching single-colour icon is
  found for it. **Change icon** lets you search for another (try the company name if nothing comes
  up). **Move up / Move down** set the order, **Delete** removes it. An empty group is hidden.
- To add a link, write `[link text](https://example.com)`. Links to your own pages work too:
  `[photos page](/photos/)`.

## 4. Save

Press **Save and publish** at the bottom.
- If something needs fixing (for example a date is missing), the field is highlighted and nothing is saved.
- After saving, the bar shows **Publishing…** and then **Live**.
- If it says **Publishing failed**, the site keeps showing the previous version. Use the link to see
  why, or ask for help.
- If it says **Couldn't check publishing**, your changes are saved; use the link to watch them go live.
- You can keep editing and save again straight away.
- If your key stops working while you save, your changes are kept: paste a new key and they are saved.
- If your text or links were changed somewhere else since you opened the admin, it reloads instead of
  overwriting; make your change again.

Every save is kept in GitHub's history, so any earlier version can be brought back.

## Lost a device?

Go to <https://github.com/settings/personal-access-tokens>, delete the `mogdhopaul admin` key,
and make a new one. The lost device can no longer change anything.
