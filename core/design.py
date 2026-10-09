"""Generate evidence-led visual direction and editable campaign prompts."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from core.market import load_policy as load_market_policy

ROOT = Path(__file__).resolve().parents[1]
DESIGN_POLICY_PATH = ROOT / "config" / "design.json"
FORMATS = {
    "instagram_feed_portrait": ("4:5", "1080x1350", "portrait feed"),
    "instagram_square": ("1:1", "1080x1080", "square feed"),
    "instagram_story": ("9:16", "1080x1920", "vertical story"),
    "whatsapp_status": ("9:16", "1080x1920", "status story"),
    "whatsapp_share_card": ("4:5", "1080x1350", "shareable card"),
}


def _s(value: Any, fallback: str = "") -> str:
    return str(value).strip() if value is not None else fallback


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value.casefold())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _find_niche(niche_id: str | None, business_type: str = "") -> dict[str, Any]:
    policy = load_market_policy()
    niches = policy["niches"]
    if niche_id:
        match = next((item for item in niches if item["id"] == niche_id), None)
        if match:
            return match
    category = _normalize(business_type)
    if category:
        matches = []
        for niche in niches:
            for alias in niche.get("aliases", []) + [niche.get("name", "")]:
                normalized = _normalize(str(alias))
                if normalized and (normalized == category or normalized in category or category in normalized):
                    matches.append((len(normalized), niche))
        if matches:
            return max(matches, key=lambda item: item[0])[1]
        return {
            "id": "context_specific",
            "name": business_type.strip(),
            "offer_angle": f"Communicate a real {business_type.strip()} service clearly.",
            "customer_problem": "Make the service understandable and its next step easy.",
            "signals_to_verify": ["real service", "audience", "brand evidence", "contact channel"],
            "search_queries": [],
            "visual_direction": {
                "style": "specific documentary commercial direction without a generic template look",
                "palette": ["observed brand colors", "natural neutrals", "one compatible accent"],
                "subject_examples": [f"a recognizable real {business_type.strip()} activity with plausible tools and setting"],
                "avoid": ["borrowed industry clichés", "decorative objects without a purpose", "unrealistic materials"],
            },
        }
    return {
        "id": "context_specific", "name": "local business",
        "offer_angle": "Communicate a real offer clearly.",
        "customer_problem": "Make the message understandable and the next step easy.",
        "signals_to_verify": ["real service", "audience", "brand evidence", "contact channel"],
        "search_queries": [],
        "visual_direction": {
            "style": "specific documentary commercial direction without a generic template look",
            "palette": ["observed brand colors", "natural neutrals", "one compatible accent"],
            "subject_examples": ["the real product or service supplied in the brief"],
            "avoid": ["borrowed industry clichés", "decorative objects without a purpose", "unrealistic materials"],
        },
    }


def build_design_brief(data: dict[str, Any]) -> dict[str, Any]:
    design_policy = json.loads(DESIGN_POLICY_PATH.read_text(encoding="utf-8"))
    brand = data.get("brand") if isinstance(data.get("brand"), dict) else {}
    business = data.get("business") if isinstance(data.get("business"), dict) else {}
    supplied_type = _s(business.get("category"))
    niche = _find_niche(_s(data.get("niche_id")) or None, supplied_type)
    format_key = _s(data.get("format"), "instagram_feed_portrait")
    ratio, dimensions, format_label = FORMATS.get(format_key, ("4:5", "1080x1350", format_key.replace("_", " ")))
    business_name = _s(business.get("name"))
    business_type = supplied_type or niche["name"] or "local business"
    observed_style = _s(brand.get("visual_style"))
    brand_source = _s(brand.get("source_url"), _s(business.get("profile_url")))
    raw_palette = brand.get("colors")
    if isinstance(raw_palette, list) and raw_palette:
        palette = [str(color).strip() for color in raw_palette[:4] if str(color).strip()]
        palette_note = "observed or supplied brand palette"
    else:
        palette = [color for color in niche["visual_direction"]["palette"] if color != "observed brand colors"][:4]
        palette_note = "provisional palette; replace it with observed brand colors"
    palette = palette or ["natural neutrals", "one compatible accent"]
    goal = _s(data.get("campaign_goal"), "promote a real service and make the next commercial step easy")
    offer = _s(data.get("offer"))
    headline = _s(data.get("headline"))
    supporting_copy = _s(data.get("supporting_copy"))
    cta = _s(data.get("cta"))
    subject_examples = niche["visual_direction"].get("subject_examples") or [f"real {business_type} activity"]
    subject = _s(data.get("main_subject"), str(subject_examples[0]))
    supplied_layout = _s(data.get("composition"))
    layout = supplied_layout or "balanced asymmetric composition, one clear focal point, and clean negative space for editable copy"
    background = _s(data.get("background"), "a specific credible setting with natural depth and few relevant elements")
    light = _s(data.get("lighting"), "soft directional natural light, coherent shadows, and real material texture")
    style = observed_style or niche["visual_direction"]["style"]
    no_text = bool(data.get("no_text_in_generated_asset", True))
    transparent = bool(data.get("transparent_background", False))
    crop = _s(data.get("crop"), "full subject or intentional crop without losing important parts")
    camera = _s(data.get("camera_angle"), "natural viewpoint consistent with the action and physically plausible perspective")
    visual_details = _s(data.get("specific_details"), "physically plausible materials, tools, surfaces, proportions, texture, and small real imperfections")
    raw_brand_colors = [str(color).strip() for color in raw_palette if str(color).strip()] if isinstance(raw_palette, list) else []
    brand_observed = bool(observed_style or raw_brand_colors or brand.get("observed") is True or _s(brand.get("research_notes")))
    forbidden = list(niche["visual_direction"].get("avoid", []))
    extra_forbidden = data.get("avoid")
    if isinstance(extra_forbidden, list):
        forbidden.extend(_s(item) for item in extra_forbidden if _s(item))
    negative = ", ".join(dict.fromkeys(forbidden + ["rendered text", "invented logos", "watermarks", "deformed elements", "decorative highlights without a purpose"]))
    background_prompt = "genuinely transparent PNG background with no false ground shadow or cutout halo" if transparent else background
    text_rule = (
        "do not include text, letters, numbers, logos, or watermarks; add copy separately as editable Canva text"
        if no_text else
        "do not invent prices, proof, dates, availability, or claims; every statement must match supplied facts"
    )
    if transparent:
        cutout_layout = supplied_layout or "centered, isolated, no scene, and no need to reserve text space inside the object"
        composition_prompt = f"full-object cutout with clean transparent margins; cutout composition: {cutout_layout}"
    else:
        composition_prompt = f"composition: {layout}; keep useful clean negative space for editable copy in {format_label}"
    image_prompt = (
        f"Create a commercial visual element for {business_type}, for {goal}. One specific focus: {subject}. "
        f"Show the action or object recognizably to someone who knows this service, without an idea collage or generic symbol. "
        f"Setting: {background_prompt}. Art direction: {style}. {composition_prompt}. Crop: {crop}. Camera: {camera}. "
        f"Lighting: {light}. Palette: {', '.join(palette)} ({palette_note}). Visual realism: {visual_details}. "
        f"Final format {format_label}, ratio {ratio}, dimensions {dimensions}. Avoid: {negative}. {text_rule}."
    )
    title_line = f"exact editable headline: '{headline}'" if headline else "reserve a clear area for a short editable headline; do not invent offer copy"
    offer_line = f"confirmed offer: '{offer}'" if offer else "do not invent price, discount, service, deadline, or benefit; leave offer copy empty until verified"
    support_line = f"exact editable supporting copy: '{supporting_copy}'" if supporting_copy else "use at most one editable support line when confirmed information exists"
    cta_line = f"single call to action: '{cta}'" if cta else "reserve an editable CTA area without inventing a link, phone number, or channel"
    magic_design_prompt = (
        f"Create an editable commercial Canva asset for {business_name or business_type}. Goal: {goal}. "
        f"Audience: potential customers of {business_type}. Format: {format_label}, {ratio}, {dimensions}. "
        f"Hierarchy: 1) {title_line}; 2) {offer_line}; 3) {support_line}; 4) {cta_line}. "
        f"Art direction: {style}. Palette: {', '.join(palette)}. Use one visual focal point, consistent alignment, generous margins, high contrast, and useful negative space. "
        "Avoid generic templates, excessive icons, gratuitous glow, shadows, gradients, and elements without a job. Do not create social proof, prices, discounts, or promises. Keep text editable."
    )
    missing_facts = []
    if not business_name:
        missing_facts.append("official business name if it must appear in the asset")
    if not brand_observed:
        missing_facts.append("observed visual identity; a URL alone does not confirm colors or style")
    if not offer:
        missing_facts.append("real service or offer to promote")
    if not headline:
        missing_facts.append("confirmed primary message")
    if not cta:
        missing_facts.append("confirmed channel and call to action")
    return {
        "status": "READY_FOR_ART_DIRECTION" if not missing_facts else "READY_WITH_FACTS_TO_VERIFY",
        "publish_ready": not missing_facts,
        "niche_id": niche["id"],
        "business": {"name": business_name or None, "category": business_type, "profile_url": brand_source or None},
        "brand_observation_status": "observed" if brand_observed else "not_observed_url_is_reference_only",
        "creative_strategy": {"goal": goal, "audience": _s(data.get("audience"), f"potential customers of {business_type} using mobile to choose and contact a provider"), "offer": offer or None, "headline": headline or None, "supporting_copy": supporting_copy or None, "cta": cta or None, "single_primary_message": True, "palette": palette, "palette_basis": palette_note, "style": style, "format": {"key": format_key, "ratio": ratio, "dimensions": dimensions}, "layout": layout},
        "magic_media_element_prompt": image_prompt,
        "magic_design_layout_prompt": magic_design_prompt,
        "canva_workflow": [
            "Inspect the real business profile, site, portfolio, and brand references.",
            "Set one goal and verify service, price, promotion, deadline, and CTA facts.",
            "Generate the visual element with the complete prompt and vary the composition if the result is generic.",
            "Compose the editable asset with hierarchy, grid, useful negative space, and no text baked into the generated image.",
            "Use a template only as a starting point; restructure anything generic.",
            "Review at mobile size for artifacts, contrast, margins, crop, spelling, commercial facts, and export format.",
            "Save the editable version and export the exact destination format.",
        ],
        "quality_gate": design_policy["quality_gate"],
        "facts_to_verify_before_publish": missing_facts,
        "do_not_publish_without_factual_copy": bool(missing_facts),
    }
