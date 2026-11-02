#!/usr/bin/env python3
"""
Brand-Conditioned Image Prompt Formatter.
Translates DESIGN.md tokens and brand_dna.json attributes into optimized,
cinematic generation prompts for Gemini Nano Banana, Imagen 3, or FLUX.
"""

import argparse
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install via pip install pyyaml", file=sys.stderr)
    sys.exit(1)

def parse_design_md(filepath):
    if not os.path.exists(filepath):
        print(f"Error: DESIGN.md not found at '{filepath}'", file=sys.stderr)
        sys.exit(1)
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    parts = re.split(r'^---[ 	]*$', content, maxsplit=2, flags=re.MULTILINE)
    tokens = {}
    if len(parts) >= 3:
        try:
            tokens = yaml.safe_load(parts[1]) or {}
        except Exception:
            pass
            
    body = parts[2] if len(parts) >= 3 else content
    
    # Extract Overview section
    overview_parts = re.split(r"(?im)^##\s+Overview", body)
    overview = overview_parts[1].split("##")[0].strip() if len(overview_parts) > 1 else ""
    
    return tokens, overview

def parse_brand_dna(filepath):
    if not filepath or not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def build_prompt(tokens, overview, dna, asset_type, user_hint):
    colors = tokens.get("colors", {})
    primary_color = colors.get("primary", "#1D54D8")
    bg_color = colors.get("background", "#F8FAFC")
    surface_color = colors.get("surface", "#FFFFFF")
    
    palette_str = f"primary {primary_color}, background canvas {bg_color}, clean surface {surface_color}"
    extra_colors = [f"{k}: {v}" for k, v in colors.items() if k not in ["primary", "background", "surface"]]
    if extra_colors:
        palette_str += ", accents: " + ", ".join(extra_colors[:3])
        
    typography = tokens.get("typography", {})
    headline_font = typography.get("headline", "clean neo-grotesque sans-serif")
    if isinstance(headline_font, dict):
        headline_font = headline_font.get("fontFamily", "sans-serif")
        
    rounded = tokens.get("rounded", "16px")
    if isinstance(rounded, dict):
        rounded = rounded.get("md", "16px")
        
    tone = dna.get("tone", ["minimalist", "focused", "modern"])
    tone_str = ", ".join(tone) if isinstance(tone, list) else str(tone)
    summary = dna.get("summary", overview)
    
    hint_str = f" featuring '{user_hint}'" if user_hint else ""

    if asset_type == "hero":
        prompt = (
            f"Ultra-high-resolution, cinematic editorial hero banner{hint_str}. "
            f"Aesthetic style: {tone_str}, visually guided by the brand philosophy: '{summary}'. "
            f"Strict brand color palette anchored by {palette_str}. "
            f"Lighting: Soft ambient studio diffusion, subtle volumetric rim illumination, zero harsh shadows. "
            f"Composition: Dynamic 16:9 wide composition with generous elegant negative space, clean geometric framing, "
            f"smooth curves with {rounded} roundedness, premium materials and modern architectural surfaces. "
            f"8k, photorealistic octane render, high fidelity, shot on 50mm f/1.8 lens."
        )
    elif asset_type == "ui":
        prompt = (
            f"Polished, high-fidelity digital UI interface preview{hint_str}. "
            f"Showcasing clean application cards with {rounded} corner radius, floating gently above a {bg_color} background. "
            f"Strict color adherence: primary interaction highlights in vibrant {primary_color}, clean white {surface_color} cards, "
            f"subtle typography in {headline_font} hierarchy. "
            f"Elevation: Soft, diffuse ambient drop shadow with multi-layered depth (0 10px 30px rgba(0,0,0,0.06)). "
            f"Aesthetic: {tone_str}, impeccably organized layout, crisp vector precision, modern SaaS excellence."
        )
    elif asset_type == "icon":
        prompt = (
            f"Minimalist 3D brand icon and application mark{hint_str}. "
            f"Smooth tactile ceramic and frosted glass material, curved with {rounded} soft radius. "
            f"Dominated by {primary_color} with subtle specular highlights and {surface_color} accents on an isolated neutral canvas. "
            f"Centered isometric perspective, studio lighting with soft diffuse reflections, macro focal depth. "
            f"Clean, iconic, instantly recognizable brand emblem."
        )
    else: # lifestyle
        prompt = (
            f"High-end editorial lifestyle photography{hint_str}. "
            f"Modern workspace context reflecting the brand tone: {tone_str}. "
            f"Visual accents thoughtfully incorporating brand colors ({primary_color}) in ambient lighting and sleek accessories. "
            f"Natural window lighting with soft afternoon diffusion, shallow depth of field, authentic tactile textures. "
            f"Shot on Hasselblad medium format, natural grading, sophisticated agency design aesthetic."
        )
        
    return prompt

def main():
    parser = argparse.ArgumentParser(description="Generate brand-conditioned image generation prompts from DESIGN.md")
    parser.add_argument("--design", required=True, help="Path to DESIGN.md file")
    parser.add_argument("--dna", default="", help="Path to optional brand_dna.json file")
    parser.add_argument("--type", choices=["hero", "ui", "lifestyle", "icon"], default="hero", help="Asset archetype")
    parser.add_argument("--hint", default="", help="Specific user hint or subject direction")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    tokens, overview = parse_design_md(args.design)
    dna = parse_brand_dna(args.dna)
    
    prompt = build_prompt(tokens, overview, dna, args.type, args.hint)
    
    if args.json:
        output = {
            "asset_type": args.type,
            "hint": args.hint,
            "prompt": prompt,
            "colors_used": tokens.get("colors", {}),
            "source_design": args.design
        }
        print(json.dumps(output, indent=2))
    else:
        print(prompt)

if __name__ == "__main__":
    main()
