# Adding travel photos

Photos are added by hand. No accounts or keys are needed.

1. Copy the photo into the `photo-originals` folder (in the site folder). Any JPG or PNG works.
   This folder stays on your computer only; it is never uploaded.
2. Open `data/photos.csv` and add one line for it:

   ```
   eiffel.jpg,"Paris, France",2025-05-14
   ```

   - **file**: the photo's file name in `photo-originals`.
   - **place**: in English. Put it in "quotes" if it has a comma. Leave it empty to show only the date.
   - **date**: when you took it, written as year-month-day.

3. In a terminal in the site folder, run:

   ```
   python -m scripts.build_photos
   ```

   It makes small, fast copies of the photos (with the camera's location data removed), puts the
   six newest on the home page and all of them on the Photos page, newest first.
   If something in the list is wrong, it says which line and changes nothing.

4. Commit and push. The site updates in a minute or two.

**To remove a photo:** delete its line from `data/photos.csv` and run the command again.

The first time on a new computer, install the one thing it needs: `python -m pip install -r scripts/requirements.txt`
