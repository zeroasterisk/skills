package main

const PackageJsonTemplate = `{
  "name": "ai-pop-artist-player",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@material/web": "^1.2.0",
    "lit": "^3.1.2"
  },
  "devDependencies": {
    "typescript": "^5.3.3",
    "vite": "^5.1.4"
  }
}`

const ViteConfigTemplate = `import { defineConfig } from 'vite';

export default defineConfig({
  root: '.',
  server: {
    port: 3000,
    open: true
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
});`

const TsConfigTemplate = `{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "node",
    "strict": true,
    "experimentalDecorators": true,
    "useDefineForClassFields": false,
    "isolatedModules": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "skipDefaultLibCheck": true
  },
  "include": ["src/**/*"]
}`

const IndexHtmlTemplate = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{.Name}} - {{.AlbumTitle}}</title>
  <meta name="description" content="{{.AlbumBio}}">
  
  <!-- Google Fonts and Material Symbols -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,1,0" rel="stylesheet">
  
  <link rel="stylesheet" href="./src/index.css">
  <script type="module" src="./src/artist-player.ts"></script>
</head>
<body>
  <artist-player></artist-player>
</body>
</html>`

const IndexCssTemplate = `:root {
  --primary-color: {{.PrimaryColor}};
  --secondary-color: {{.SecondaryColor}};
  --bg-color: #08080c;
  --surface-color: rgba(18, 18, 26, 0.45);
  --surface-border: rgba(255, 255, 255, 0.08);
  --text-primary: #f3f4f6;
  --text-secondary: #a1a5b3;
  
  /* Material 3 token overrides */
  --md-sys-color-primary: var(--primary-color);
  --md-sys-color-primary-container: rgba(255, 255, 255, 0.04);
  --md-sys-color-on-primary-container: #ffffff;
  --md-sys-color-surface: #08080c;
  --md-sys-color-on-surface: var(--text-primary);
  --md-sys-color-outline: var(--surface-border);
}

body {
  margin: 0;
  padding: 0;
  font-family: 'Outfit', sans-serif;
  background: radial-gradient(circle at 50% 0%, rgba({{.PrimaryRGB}}, 0.16) 0%, #08080c 80%);
  background-attachment: fixed;
  color: var(--text-primary);
  min-height: 100vh;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
}

::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.3);
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.22);
}
`

const ArtistPlayerTemplate = `import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import '@material/web/iconbutton/filled-icon-button.js';
import '@material/web/icon/icon.js';
import '@material/web/slider/slider.js';
import '@material/web/chips/filter-chip.js';
import '@material/web/chips/chip-set.js';

// Parsed and injected at compilation time
const artistData = {{.ArtistJSONEmbed}};

@customElement('artist-player')
export class ArtistPlayer extends LitElement {
  @state() private activeTrackIndex = 0;
  @state() private isPlaying = false;
  @state() private currentTime = 0;
  @state() private duration = 0;
  @state() private volume = 0.8;
  @state() private activeTab = 'tracks'; // 'tracks' | 'bio' | 'album'

  private audio!: HTMLAudioElement;

  static override styles = cssBACKTICK
    :host {
      display: block;
      width: 100%;
      max-width: 1200px;
      margin: 0 auto;
      padding: 32px 16px;
      box-sizing: border-box;
    }

    .glass-card {
      background: rgba(22, 22, 32, 0.5);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 24px;
      padding: 32px;
      box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.5);
    }

    /* Grid Layout */
    .dashboard {
      display: grid;
      grid-template-columns: 450px 1fr;
      gap: 32px;
    }

    @media (max-width: 950px) {
      .dashboard {
        grid-template-columns: 1fr;
      }
    }

    /* Left Player Pane */
    .player-pane {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
    }

    .cover-art-container {
      position: relative;
      width: 320px;
      height: 320px;
      border-radius: 20px;
      overflow: hidden;
      box-shadow: 0 15px 35px rgba(0, 0, 0, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.1);
      margin-bottom: 24px;
      transition: transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }

    .cover-art-container:hover {
      transform: scale(1.03);
    }

    .cover-art-container img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .cover-art-overlay {
      position: absolute;
      top: 12px;
      right: 12px;
      background: rgba(0, 0, 0, 0.6);
      backdrop-filter: blur(8px);
      padding: 6px 12px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 1px;
      text-transform: uppercase;
      color: var(--primary-color);
      border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .artist-info-header {
      margin-bottom: 16px;
    }

    .artist-info-header h1 {
      margin: 0 0 6px 0;
      font-size: 28px;
      font-weight: 800;
      letter-spacing: -0.5px;
      background: linear-gradient(135deg, #ffffff 0%, #b8b8c7 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .track-title-player {
      margin: 0;
      font-size: 18px;
      font-weight: 500;
      color: var(--primary-color);
      height: 24px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      width: 380px;
    }

    .controls-row {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 16px;
      margin: 24px 0 16px 0;
    }

    .play-btn {
      --md-filled-icon-button-container-width: 64px;
      --md-filled-icon-button-container-height: 64px;
      --md-filled-icon-button-icon-size: 32px;
      --md-sys-color-primary: var(--primary-color);
      box-shadow: 0 4px 15px rgba(var(--primary-rgb), 0.4);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .play-btn:hover {
      transform: scale(1.05);
      box-shadow: 0 6px 20px rgba(var(--primary-rgb), 0.6);
    }

    .secondary-control {
      --md-filled-icon-button-container-width: 48px;
      --md-filled-icon-button-container-height: 48px;
      --md-filled-icon-button-icon-size: 22px;
      --md-sys-color-primary: rgba(255, 255, 255, 0.08);
      --md-sys-color-on-primary: var(--text-primary);
    }

    .secondary-control:hover {
      --md-sys-color-primary: rgba(255, 255, 255, 0.16);
    }

    .progress-bar-container {
      width: 100%;
      max-width: 380px;
      margin-bottom: 12px;
    }

    .progress-slider {
      width: 100%;
      --md-slider-active-track-color: var(--primary-color);
      --md-slider-inactive-track-color: rgba(255, 255, 255, 0.12);
      --md-slider-handle-color: var(--primary-color);
    }

    .time-labels {
      display: flex;
      justify-content: space-between;
      width: 100%;
      max-width: 380px;
      font-size: 12px;
      color: var(--text-secondary);
      padding: 0 6px;
      box-sizing: border-box;
    }

    .volume-container {
      display: flex;
      align-items: center;
      gap: 12px;
      width: 100%;
      max-width: 200px;
      margin-top: 16px;
      color: var(--text-secondary);
    }

    .volume-slider {
      width: 100%;
      --md-slider-active-track-color: var(--text-secondary);
      --md-slider-inactive-track-color: rgba(255, 255, 255, 0.08);
      --md-slider-handle-color: var(--text-secondary);
    }

    /* Right Navigation & Details Pane */
    .details-pane {
      display: flex;
      flex-direction: column;
    }

    .navigation-tabs {
      display: flex;
      gap: 8px;
      border-bottom: 1px solid var(--surface-border);
      padding-bottom: 12px;
      margin-bottom: 24px;
    }

    .tab-button {
      background: none;
      border: none;
      color: var(--text-secondary);
      font-family: 'Outfit', sans-serif;
      font-size: 15px;
      font-weight: 600;
      padding: 8px 16px;
      cursor: pointer;
      border-radius: 12px;
      transition: all 0.2s ease;
    }

    .tab-button:hover {
      color: var(--text-primary);
      background: rgba(255, 255, 255, 0.04);
    }

    .tab-button.active {
      color: #ffffff;
      background: var(--primary-color);
      box-shadow: 0 4px 12px rgba(var(--primary-rgb), 0.25);
    }

    .tab-content {
      flex: 1;
      overflow-y: auto;
      max-height: 480px;
      padding-right: 8px;
    }

    /* Tracks List */
    .track-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .track-card {
      display: grid;
      grid-template-columns: 50px 60px 1fr auto;
      align-items: center;
      gap: 16px;
      padding: 12px 16px;
      border-radius: 16px;
      border: 1px solid rgba(255, 255, 255, 0.04);
      background: rgba(255, 255, 255, 0.01);
      cursor: pointer;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .track-card:hover {
      background: rgba(255, 255, 255, 0.04);
      border-color: rgba(255, 255, 255, 0.08);
      transform: translateX(4px);
    }

    .track-card.active {
      background: rgba(var(--primary-rgb), 0.08);
      border-color: rgba(var(--primary-rgb), 0.2);
    }

    .track-idx {
      font-weight: 700;
      color: var(--text-secondary);
      font-size: 14px;
      text-align: center;
    }

    .track-card.active .track-idx {
      color: var(--primary-color);
    }

    .track-art-thumb {
      width: 50px;
      height: 50px;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .track-art-thumb img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .track-meta {
      overflow: hidden;
    }

    .track-title {
      margin: 0 0 4px 0;
      font-size: 16px;
      font-weight: 600;
      color: #ffffff;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .track-card.active .track-title {
      color: var(--primary-color);
    }

    .track-desc {
      margin: 0;
      font-size: 13px;
      color: var(--text-secondary);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* Micro Soundwave Animation for Active Track */
    .wave-animation {
      display: flex;
      align-items: flex-end;
      gap: 3px;
      height: 18px;
      padding-right: 4px;
    }

    .wave-bar {
      width: 3px;
      background: var(--primary-color);
      border-radius: 2px;
      animation: bounce 1s infinite alternate;
    }

    .wave-bar:nth-child(2) { animation-delay: 0.15s; }
    .wave-bar:nth-child(3) { animation-delay: 0.3s; }
    .wave-bar:nth-child(4) { animation-delay: 0.45s; }

    @keyframes bounce {
      0% { height: 3px; }
      100% { height: 16px; }
    }

    /* About Tabs Content */
    .bio-container, .album-container {
      line-height: 1.6;
      font-size: 15px;
      color: var(--text-secondary);
    }

    .bio-container p, .album-container p {
      margin-top: 0;
      margin-bottom: 16px;
    }

    .bio-title, .album-title-detail {
      font-size: 22px;
      font-weight: 700;
      color: #ffffff;
      margin-top: 0;
      margin-bottom: 12px;
    }

    .chip-list {
      margin-top: 24px;
    }

    /* Lyrics Display Component */
    .lyrics-panel {
      margin-top: 24px;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 16px;
      padding: 16px 20px;
      border: 1px solid rgba(255, 255, 255, 0.03);
    }

    .lyrics-header {
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      font-weight: 700;
      color: var(--primary-color);
      margin-bottom: 8px;
    }

    .lyrics-content {
      font-size: 14px;
      white-space: pre-wrap;
      line-height: 1.7;
      color: var(--text-primary);
      max-height: 150px;
      overflow-y: auto;
      font-style: italic;
    }
  BACKTICK;

  override firstUpdated() {
    this.initAudio();
  }

  private initAudio() {
    // Standard initialization of HTML5 audio stream
    const activeTrack = artistData.tracks[this.activeTrackIndex];
    const sourcePath = 'assets/' + (activeTrack.fileMp3 || activeTrack.file);
    
    this.audio = new Audio(sourcePath);
    this.audio.volume = this.volume;

    // Events
    this.audio.addEventListener('timeupdate', () => {
      this.currentTime = this.audio.currentTime;
    });

    this.audio.addEventListener('durationchange', () => {
      this.duration = this.audio.duration || 0;
    });

    this.audio.addEventListener('ended', () => {
      this.playNext();
    });
  }

  private togglePlay() {
    if (this.isPlaying) {
      this.audio.pause();
      this.isPlaying = false;
    } else {
      this.audio.play()
        .then(() => { this.isPlaying = true; })
        .catch(err => console.error("Playback error:", err));
    }
  }

  private playTrack(index: number) {
    if (index === this.activeTrackIndex) {
      this.togglePlay();
      return;
    }

    this.audio.pause();
    this.activeTrackIndex = index;
    const activeTrack = artistData.tracks[index];
    const sourcePath = 'assets/' + (activeTrack.fileMp3 || activeTrack.file);
    
    this.audio.src = sourcePath;
    this.audio.load();
    this.audio.play()
      .then(() => { this.isPlaying = true; })
      .catch(err => console.error("Playback error on load:", err));
  }

  private playNext() {
    const nextIndex = (this.activeTrackIndex + 1) % artistData.tracks.length;
    this.playTrack(nextIndex);
  }

  private playPrev() {
    let prevIndex = this.activeTrackIndex - 1;
    if (prevIndex < 0) {
      prevIndex = artistData.tracks.length - 1;
    }
    this.playTrack(prevIndex);
  }

  private handleSeek(e: any) {
    const value = e.target.value;
    this.audio.currentTime = value;
    this.currentTime = value;
  }

  private handleVolume(e: any) {
    const vol = e.target.value;
    this.audio.volume = vol;
    this.volume = vol;
  }

  private formatTime(secs: number): string {
    if (isNaN(secs) || secs === 0) return '0:00';
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return BACKTICK${m}:${s < 10 ? '0' : ''}${s}BACKTICK;
  }

  override render() {
    const activeTrack = artistData.tracks[this.activeTrackIndex];

    return htmlBACKTICK
      <div class="glass-card dashboard">
        <!-- Left Pane: Playback, cover art, track info, lyrics -->
        <div class="player-pane">
          <div class="cover-art-container">
            <img src="assets/${activeTrack.art || artistData.albumArt}" alt="${activeTrack.title}" />
            <div class="cover-art-overlay">${artistData.genre}</div>
          </div>

          <div class="artist-info-header">
            <h1>${artistData.name}</h1>
            <p class="track-title-player">${activeTrack.title}</p>
          </div>

          <!-- Slider -->
          <div class="progress-bar-container">
            <md-slider
              class="progress-slider"
              min="0"
              max="${this.duration}"
              value="${this.currentTime}"
              @input="${this.handleSeek}"
            ></md-slider>
          </div>

          <div class="time-labels">
            <span>${this.formatTime(this.currentTime)}</span>
            <span>${this.formatTime(this.duration || 120)}</span>
          </div>

          <!-- Controls -->
          <div class="controls-row">
            <md-filled-icon-button
              class="secondary-control"
              @click="${this.playPrev}"
            >
              <md-icon>skip_previous</md-icon>
            </md-filled-icon-button>

            <md-filled-icon-button
              class="play-btn"
              @click="${this.togglePlay}"
            >
              <md-icon>${this.isPlaying ? 'pause' : 'play_arrow'}</md-icon>
            </md-filled-icon-button>

            <md-filled-icon-button
              class="secondary-control"
              @click="${this.playNext}"
            >
              <md-icon>skip_next</md-icon>
            </md-filled-icon-button>
          </div>

          <!-- Volume -->
          <div class="volume-container">
            <md-icon>${this.volume === 0 ? 'volume_off' : this.volume < 0.4 ? 'volume_down' : 'volume_up'}</md-icon>
            <md-slider
              class="volume-slider"
              min="0"
              max="1"
              step="0.05"
              value="${this.volume}"
              @input="${this.handleVolume}"
            ></md-slider>
          </div>

          <!-- Lyrics Display -->
          ${activeTrack.lyrics ? htmlBACKTICK
            <div class="lyrics-panel" style="width: 100%; max-width: 380px; text-align: left; box-sizing: border-box;">
              <div class="lyrics-header">Spoken Lyrics</div>
              <div class="lyrics-content">${activeTrack.lyrics}</div>
            </div>
          BACKTICK : ''}
        </div>

        <!-- Right Pane: Tabs (Tracks, Artist Bio, Album narrative) -->
        <div class="details-pane">
          <div class="navigation-tabs">
            <button
              class="tab-button ${this.activeTab === 'tracks' ? 'active' : ''}"
              @click="${() => this.activeTab = 'tracks'}"
            >Tracks</button>
            <button
              class="tab-button ${this.activeTab === 'bio' ? 'active' : ''}"
              @click="${() => this.activeTab = 'bio'}"
            >About Artist</button>
            <button
              class="tab-button ${this.activeTab === 'album' ? 'active' : ''}"
              @click="${() => this.activeTab = 'album'}"
            >The Concept</button>
          </div>

          <div class="tab-content">
            <!-- Tab: Track List -->
            ${this.activeTab === 'tracks' ? htmlBACKTICK
              <div class="track-list">
                ${artistData.tracks.map((track: any, idx: number) => htmlBACKTICK
                  <div
                    class="track-card ${idx === this.activeTrackIndex ? 'active' : ''}"
                    @click="${() => this.playTrack(idx)}"
                  >
                    <div class="track-idx">
                      ${idx === this.activeTrackIndex && this.isPlaying ? htmlBACKTICK
                        <div class="wave-animation">
                          <div class="wave-bar"></div>
                          <div class="wave-bar"></div>
                          <div class="wave-bar"></div>
                          <div class="wave-bar"></div>
                        </div>
                      BACKTICK : htmlBACKTICK0${idx + 1}BACKTICK}
                    </div>
                    <div class="track-art-thumb">
                      <img src="assets/${track.art || artistData.albumArt}" alt="${track.title}" />
                    </div>
                    <div class="track-meta">
                      <h4 class="track-title">${track.title}</h4>
                      <p class="track-desc">${track.description}</p>
                    </div>
                    <div>
                      <md-filled-icon-button
                        class="secondary-control"
                        style="--md-filled-icon-button-container-width: 36px; --md-filled-icon-button-container-height: 36px; --md-filled-icon-button-icon-size: 18px;"
                      >
                        <md-icon>${idx === this.activeTrackIndex && this.isPlaying ? 'pause' : 'play_arrow'}</md-icon>
                      </md-filled-icon-button>
                    </div>
                  </div>
                BACKTICK)}
              </div>
            BACKTICK : ''}

            <!-- Tab: Artist Bio -->
            ${this.activeTab === 'bio' ? htmlBACKTICK
              <div class="bio-container">
                <h3 class="bio-title">${artistData.name} Biography</h3>
                ${artistData.bio.split('\n\n').map((paragraph: string) => htmlBACKTICK<p>${paragraph}</p>BACKTICK)}
                
                <div class="chip-list">
                  <md-chip-set>
                    ${artistData.tags.map((tag: string) => htmlBACKTICK
                      <md-filter-chip label="${tag}" selected></md-filter-chip>
                    BACKTICK)}
                  </md-chip-set>
                </div>
              </div>
            BACKTICK : ''}

            <!-- Tab: Album narrative -->
            ${this.activeTab === 'album' ? htmlBACKTICK
              <div class="album-container">
                <h3 class="bio-title">${artistData.albumTitle}</h3>
                ${artistData.albumBio.split('\n\n').map((paragraph: string) => htmlBACKTICK<p>${paragraph}</p>BACKTICK)}
              </div>
            BACKTICK : ''}
          </div>
        </div>
      </div>
    BACKTICK;
  }
}
`
