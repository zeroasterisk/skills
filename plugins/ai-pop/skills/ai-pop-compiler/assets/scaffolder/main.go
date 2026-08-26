package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"text/template"
)

// Artist definition matching artist.json structure
type Track struct {
	ID          string `json:"id"`
	Title       string `json:"title"`
	File        string `json:"file"`
	FileMp3     string `json:"fileMp3"`
	Art         string `json:"art"`
	Description string `json:"description"`
	Lyrics      string `json:"lyrics"`
}

type Artist struct {
	Name           string   `json:"name"`
	Genre          string   `json:"genre"`
	Tags           []string `json:"tags"`
	Theme          string   `json:"theme"`
	Bio            string   `json:"bio"`
	PrimaryColor   string   `json:"primaryColor"`
	SecondaryColor string   `json:"secondaryColor"`
	AlbumTitle     string   `json:"albumTitle"`
	AlbumBio       string   `json:"albumBio"`
	AlbumArt       string   `json:"albumArt"`
	Tracks         []Track  `json:"tracks"`
}

func main() {
	dirFlag := flag.String("dir", ".", "Directory of the artist project containing artist.json")
	flag.Parse()

	// 1. Resolve paths
	absDir, err := filepath.Abs(*dirFlag)
	if err != nil {
		fmt.Printf("Error resolving path: %v\n", err)
		os.Exit(1)
	}

	jsonPath := filepath.Join(absDir, "artist.json")
	if _, err := os.Stat(jsonPath); os.IsNotExist(err) {
		fmt.Printf("Error: artist.json not found in directory %s\n", absDir)
		os.Exit(1)
	}

	// 2. Parse artist.json
	fmt.Printf("Reading and parsing %s...\n", jsonPath)
	fileBytes, err := os.ReadFile(jsonPath)
	if err != nil {
		fmt.Printf("Error reading artist.json: %v\n", err)
		os.Exit(1)
	}

	var artist Artist
	if err := json.Unmarshal(fileBytes, &artist); err != nil {
		fmt.Printf("Error parsing JSON: %v\n", err)
		os.Exit(1)
	}

	// Calculate RGB representation for background radial glow
	artistPrimaryRGB := hexToRGB(artist.PrimaryColor)

	// 3. Create directory layout
	webDir := filepath.Join(absDir, "web")
	publicDir := filepath.Join(webDir, "public")
	assetsDir := filepath.Join(publicDir, "assets")
	srcDir := filepath.Join(webDir, "src")

	dirs := []string{webDir, publicDir, assetsDir, srcDir}
	for _, d := range dirs {
		if err := os.MkdirAll(d, 0755); err != nil {
			fmt.Printf("Error creating directory %s: %v\n", d, err)
			os.Exit(1)
		}
	}

	// 4. Copy assets into public/assets/ and rewrite asset names
	fmt.Println("Copying generated media assets to web static directory...")

	// Helper function to copy file
	copyFile := func(srcName string) (string, error) {
		if srcName == "" {
			return "", nil
		}
		srcFile := filepath.Join(absDir, srcName)
		dstName := filepath.Base(srcName)
		dstFile := filepath.Join(assetsDir, dstName)

		if _, err := os.Stat(srcFile); os.IsNotExist(err) {
			fmt.Printf("Warning: Asset file not found: %s\n", srcFile)
			return dstName, nil // Don't crash, let compilation proceed
		}

		in, err := os.Open(srcFile)
		if err != nil {
			return "", err
		}
		defer in.Close()

		out, err := os.Create(dstFile)
		if err != nil {
			return "", err
		}
		defer out.Close()

		if _, err = io.Copy(out, in); err != nil {
			return "", err
		}
		fmt.Printf("  Copied %s -> %s\n", srcName, dstName)
		return dstName, nil
	}

	// Copy album cover
	_, _ = copyFile(artist.AlbumArt)

	// Copy track assets
	for i, t := range artist.Tracks {
		_, _ = copyFile(t.File)
		_, _ = copyFile(t.FileMp3)
		_, _ = copyFile(t.Art)

		// Sanitize paths for embedded JSON inside Lit element
		if t.File != "" {
			artist.Tracks[i].File = filepath.Base(t.File)
		}
		if t.FileMp3 != "" {
			artist.Tracks[i].FileMp3 = filepath.Base(t.FileMp3)
		} else {
			artist.Tracks[i].FileMp3 = ""
		}
		if t.Art != "" {
			artist.Tracks[i].Art = filepath.Base(t.Art)
		}
	}
	artist.AlbumArt = filepath.Base(artist.AlbumArt)

	// Serialize the updated artist details with local paths to embed in the frontend code
	artistJSONBytes, err := json.MarshalIndent(artist, "", "  ")
	if err != nil {
		fmt.Printf("Error serializing artist metadata for embedding: %v\n", err)
		os.Exit(1)
	}

	// 5. Build templates data
	tmplData := struct {
		Name             string
		Genre            string
		Theme            string
		Bio              string
		PrimaryColor     string
		SecondaryColor   string
		PrimaryRGB       string
		AlbumTitle       string
		AlbumBio         string
		AlbumArt         string
		ArtistJSONEmbed  string
		ArtistData       Artist
	}{
		Name:             artist.Name,
		Genre:            artist.Genre,
		Theme:            artist.Theme,
		Bio:              artist.Bio,
		PrimaryColor:     artist.PrimaryColor,
		SecondaryColor:   artist.SecondaryColor,
		PrimaryRGB:       artistPrimaryRGB,
		AlbumTitle:       artist.AlbumTitle,
		AlbumBio:         artist.AlbumBio,
		AlbumArt:         artist.AlbumArt,
		ArtistJSONEmbed:  string(artistJSONBytes),
		ArtistData:       artist,
	}

	// 6. Generate frontend files from templates
	filesToWrite := []struct {
		Path     string
		Content  string
		Template bool
	}{
		{filepath.Join(webDir, "package.json"), PackageJsonTemplate, false},
		{filepath.Join(webDir, "vite.config.js"), ViteConfigTemplate, false},
		{filepath.Join(webDir, "tsconfig.json"), TsConfigTemplate, false},
		{filepath.Join(webDir, "index.html"), IndexHtmlTemplate, true},
		{filepath.Join(srcDir, "index.css"), IndexCssTemplate, true},
		{filepath.Join(srcDir, "artist-player.ts"), ArtistPlayerTemplate, true},
	}

	for _, f := range filesToWrite {
		fmt.Printf("Generating file %s...\n", filepath.Base(f.Path))
		var fileContent string
		if f.Template {
			tmpl, err := template.New(filepath.Base(f.Path)).Parse(f.Content)
			if err != nil {
				fmt.Printf("Error parsing template for %s: %v\n", f.Path, err)
				os.Exit(1)
			}
			var builder strings.Builder
			if err := tmpl.Execute(&builder, tmplData); err != nil {
				fmt.Printf("Error executing template for %s: %v\n", f.Path, err)
				os.Exit(1)
			}
			fileContent = builder.String()
			fileContent = strings.ReplaceAll(fileContent, "BACKTICK", "`")
		} else {
			fileContent = f.Content
			fileContent = strings.ReplaceAll(fileContent, "BACKTICK", "`")
		}

		if err := os.WriteFile(f.Path, []byte(fileContent), 0644); err != nil {
			fmt.Printf("Error writing file %s: %v\n", f.Path, err)
			os.Exit(1)
		}
	}

	fmt.Println("\n🎉 Scaffolding successfully compiled! Web player files written inside the 'web' directory.")
	fmt.Println("\nTo run the player locally, run these commands:")
	fmt.Printf("  cd %s\n", filepath.Join(absDir, "web"))
	fmt.Println("  npm install")
	fmt.Println("  npm run dev")
	fmt.Println("")
}

// Convert Hex color to "r, g, b" string for alpha glow effects
func hexToRGB(hex string) string {
	hex = strings.TrimPrefix(hex, "#")
	if len(hex) == 3 {
		hex = string([]byte{hex[0], hex[0], hex[1], hex[1], hex[2], hex[2]})
	}
	if len(hex) != 6 {
		return "98, 0, 238" // Default fallback purple
	}
	var r, g, b uint8
	fmt.Sscanf(hex, "%02x%02x%02x", &r, &g, &b)
	return fmt.Sprintf("%d, %d, %d", r, g, b)
}
