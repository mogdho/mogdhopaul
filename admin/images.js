// Resize a photo in the browser. Re-encoding through a canvas drops EXIF data (including GPS location),
// so the original file never leaves the device.
import { targetSize } from './core.js';

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
