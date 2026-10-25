# CoachMe v3 — YouTube upload package

All assets are **2:04.32**, 1600×900, and synchronized to the same video timeline.
Use the English-card video as the main upload; the other languages are separate
audio and subtitle tracks.

## Files

| File | Purpose |
|---|---|
| `CoachMe-YouTube-Master-English.mp4` | Main video — English title card + English audio |
| `CoachMe-YouTube-Master-English-Silent.mp4` | Silent version of the same video, if Studio asks for a silent master |
| `CoachMe-Audio-English.m4a` | English audio track |
| `CoachMe-Audio-Chinese.m4a` | Chinese audio track |
| `CoachMe-Audio-Hebrew.m4a` | Hebrew audio track |
| `CoachMe-Audio-Russian.m4a` | Russian audio track |
| `CoachMe-Subtitles-English.srt` | English captions |
| `CoachMe-Subtitles-Chinese.srt` | Chinese captions |
| `CoachMe-Subtitles-Hebrew.srt` | Hebrew captions (RTL bidi controls included) |
| `CoachMe-Subtitles-Russian.srt` | Russian captions |
| `Thumbnail-English.png` | Suggested thumbnail |

## Upload steps

1. Upload **`CoachMe-YouTube-Master-English.mp4`** as the main video.
2. In YouTube Studio on desktop, open the video and add the additional audio tracks:
   - `CoachMe-Audio-Chinese.m4a`
   - `CoachMe-Audio-Hebrew.m4a`
   - `CoachMe-Audio-Russian.m4a`
   - English is already the primary audio. Add `CoachMe-Audio-English.m4a` only if Studio asks for a separate English track.
3. Add the four subtitle tracks:
   - `CoachMe-Subtitles-English.srt` → English
   - `CoachMe-Subtitles-Chinese.srt` → Chinese (Simplified)
   - `CoachMe-Subtitles-Hebrew.srt` → Hebrew
   - `CoachMe-Subtitles-Russian.srt` → Russian
4. If YouTube Studio requires a **silent master** before adding all audio tracks:
   - Upload `CoachMe-YouTube-Master-English-Silent.mp4`
   - Add all four `.m4a` tracks, including English.

## If multi-language audio is not available

YouTube’s Multi-language audio feature is not available on every channel or
region. If Studio does not show it, upload the four language videos separately
from the `demo/` folder:

- `CoachMe-Demo-English.mp4`
- `CoachMe-Demo-Chinese.mp4`
- `CoachMe-Demo-Hebrew.mp4`
- `CoachMe-Demo-Russian.mp4`

Each one has its own language title card, narration, and matching SRT in this
package.

## Notes

- The English video is the YouTube master.
- The app body is identical in all four language versions after the 3.5 s title card; only the card differs.
- Narration starts at **0:00.5**, so the card is visible before the voice begins.
- Hebrew subtitles include Unicode RLE/PDF bidi controls for correct right-to-left display.
- Native speakers should review the Chinese, Hebrew and Russian narration and terminology before publishing.
