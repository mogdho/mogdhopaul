// Resize a photo in the browser. Re-encoding through a canvas drops EXIF data (including GPS location),
// so the original file never leaves the device.
import { cropRect, targetSize } from './core.js';

// Profile photo files, in the 4:5 shape of the frame beside the name on the home page.
// small -> /mogdhopaul.webp (the page), large -> /mogdhopaul.jpeg (fallback and link previews).
export const PORTRAIT_SIZE = { small: { width: 480, height: 600 }, large: { width: 960, height: 1200 } };

/**
 * Cut `file` to the shape of `size`, keeping the part chosen by `focus` ({x, y} percentages).
 * WebP by default (JPEG where the browser can't make WebP); { jpeg: true } always gives JPEG.
 */
export async function cropImage(file, focus, size, { jpeg = false } = {}) {
  const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
  const r = cropRect(bitmap.width, bitmap.height, size.width, size.height, focus);
  const canvas = document.createElement('canvas');
  canvas.width = r.outW;
  canvas.height = r.outH;
  const ctx = canvas.getContext('2d');
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(bitmap, r.sx, r.sy, r.sw, r.sh, 0, 0, r.outW, r.outH);
  bitmap.close();
  const toBlob = (type) => new Promise((resolve) => canvas.toBlob(resolve, type, 0.85));
  let blob = jpeg ? null : await toBlob('image/webp');
  // Safari can't make WebP; browsers read a JPEG fine even from a .webp address.
  if (!blob || (!jpeg && blob.type !== 'image/webp')) blob = await toBlob('image/jpeg');
  if (!blob) throw new Error('This browser could not prepare the photo.');
  return blob;
}

export async function resizeImage(file, maxWidth) {
  const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
  const { width, height } = targetSize(bitmap.width, bitmap.height, maxWidth);
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  canvas.getContext('2d').drawImage(bitmap, 0, 0, width, height);
  bitmap.close();
  const toBlob = (type) => new Promise((resolve) => canvas.toBlob(resolve, type, 0.8));
  let blob = await toBlob('image/webp');
  let ext = 'webp';
  if (!blob || blob.type !== 'image/webp') {
    blob = await toBlob('image/jpeg');
    ext = 'jpg';
  }
  if (!blob) throw new Error('This browser could not prepare the photo.');
  return { blob, width, height, ext };
}
