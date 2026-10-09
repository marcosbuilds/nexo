"""Generate context-specific art direction and rich prompts for Canva AI."""
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
    "instagram_feed_portrait": ("4:5", "1080x1350", "feed vertical"),
    "instagram_square": ("1:1", "1080x1080", "feed quadrado"),
    "instagram_story": ("9:16", "1080x1920", "story vertical"),
    "whatsapp_status": ("9:16", "1080x1920", "Status do WhatsApp"),
    "whatsapp_share_card": ("4:5", "1080x1350", "peça compartilhável no WhatsApp"),
}


def _s(value: Any, fallback: str = "") -> str:
    return str(value).strip() if value is not None else fallback


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value.casefold())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _find_niche(niche_id: str | None, business_type: str = "") -> dict[str, Any]:
    """Use an explicit niche or a category match; never silently style every business as a barber."""
    policy = load_market_policy()
    niches = policy["niches"]
    if niche_id:
        match = next((x for x in niches if x["id"] == niche_id), None)
        if match:
            return match
    category = _normalize(business_type)
    if category:
        matches = []
        for niche in niches:
            for alias in niche.get("aliases", []) + [niche.get("name", "")]:
                norm_alias = _normalize(str(alias))
                if norm_alias and (norm_alias == category or norm_alias in category or category in norm_alias):
                    matches.append((len(norm_alias), niche))
        if matches:
            return max(matches, key=lambda item: item[0])[1]
        # Unknown industries get a neutral art direction rather than borrowed niche clichés.
        return {
            "id": "context_specific",
            "name": business_type.strip(),
            "offer_angle": f"Comunicar um serviço real de {business_type.strip()} com clareza.",
            "customer_problem": "Tornar o serviço compreensível e facilitar o próximo passo.",
            "signals_to_verify": ["serviço real", "público", "identidade visual", "canal de contato"],
            "search_queries": [],
            "visual_direction": {
                "style": "fotografia documental comercial natural, específica para a atividade real e sem estética de template",
                "palette": ["cores reais da marca", "neutros naturais", "um único acento observado na identidade"],
                "subject_examples": [f"uma ação real e reconhecível de {business_type.strip()}, com ferramentas e ambiente plausíveis"],
                "avoid": ["clichês visuais de outros setores", "objetos decorativos sem função", "materiais e proporções irreais"],
            },
        }
    # No category means no justified industry assumption. Use a neutral brief until context is supplied.
    return {
        "id": "context_specific", "name": "negócio local",
        "offer_angle": "Comunicar uma oferta real com clareza.",
        "customer_problem": "Tornar a mensagem compreensível e facilitar o próximo passo.",
        "signals_to_verify": ["serviço real", "público", "identidade visual", "canal de contato"],
        "search_queries": [],
        "visual_direction": {
            "style": "fotografia documental comercial natural, específica para o negócio real e sem estética de template",
            "palette": ["cores reais da marca", "neutros naturais", "um único acento observado na identidade"],
            "subject_examples": ["o serviço ou produto real informado no briefing, em um ambiente plausível"],
            "avoid": ["clichês visuais de um setor presumido", "objetos decorativos sem função", "materiais e proporções irreais"],
        },
    }


def build_design_brief(data: dict[str, Any]) -> dict[str, Any]:
    design_policy = json.loads(DESIGN_POLICY_PATH.read_text(encoding="utf-8"))
    brand = data.get("brand") if isinstance(data.get("brand"), dict) else {}
    business = data.get("business") if isinstance(data.get("business"), dict) else {}
    supplied_business_type = _s(business.get("category"), "")
    niche = _find_niche(_s(data.get("niche_id")) or None, supplied_business_type)
    fmt_key = _s(data.get("format"), "instagram_feed_portrait")
    ratio, dimensions, format_label = FORMATS.get(fmt_key, ("4:5", "1080x1350", fmt_key.replace("_", " ")))

    business_name = _s(business.get("name"), "")
    business_type = supplied_business_type or niche["name"] or "negócio local"
    observed_style = _s(brand.get("visual_style"), "")
    brand_source = _s(brand.get("source_url"), _s(business.get("profile_url"), ""))
    raw_palette = brand.get("colors")
    if isinstance(raw_palette, list) and raw_palette:
        palette = [str(c).strip() for c in raw_palette[:4] if str(c).strip()]
        palette_note = "paleta observada/fornecida pela marca"
    else:
        palette = [c for c in niche["visual_direction"]["palette"] if c != "cores reais da marca"][:4]
        palette_note = "paleta provisória para o conceito; substituir pelas cores reais se forem encontradas"
    if not palette:
        palette = ["neutros naturais", "um acento coerente com a marca"]

    goal = _s(data.get("campaign_goal"), "divulgar um serviço real e facilitar o próximo passo comercial")
    offer = _s(data.get("offer"), "")
    headline = _s(data.get("headline"), "")
    supporting_copy = _s(data.get("supporting_copy"), "")
    cta = _s(data.get("cta"), "")
    subject_examples = niche["visual_direction"].get("subject_examples") or [f"atividade real de {business_type}"]
    subject = _s(data.get("main_subject"), str(subject_examples[0]))
    supplied_layout = _s(data.get("composition"), "")
    layout = supplied_layout or "composição assimétrica equilibrada, foco visual principal bem definido e espaço negativo limpo no lado oposto para texto editável"
    background = _s(data.get("background"), "ambiente específico e crível para o serviço, com profundidade natural e poucos elementos relevantes")
    light = _s(data.get("lighting"), "luz natural suave e direcional, sombras coerentes e textura de materiais real")
    style = observed_style or niche["visual_direction"]["style"]
    no_text = bool(data.get("no_text_in_generated_asset", True))
    transparent = bool(data.get("transparent_background", False))
    crop = _s(data.get("crop"), "sujeito inteiro ou enquadrado de forma intencional, sem cortar partes importantes")
    camera = _s(data.get("camera_angle"), "ponto de vista natural coerente com a ação, perspectiva fisicamente plausível, sem lente exagerada")
    required_visual_details = _s(data.get("specific_details"), "materiais, ferramentas, superfícies e proporções fisicamente plausíveis; textura natural, pequenas imperfeições reais e nada com aparência plástica")
    raw_brand_colors = [str(c).strip() for c in raw_palette if str(c).strip()] if isinstance(raw_palette, list) else []
    brand_observed = bool(observed_style or raw_brand_colors or brand.get("observed") is True or _s(brand.get("research_notes")))
    forbidden = list(niche["visual_direction"].get("avoid", []))
    extra_forbidden = data.get("avoid")
    if isinstance(extra_forbidden, list):
        forbidden.extend(_s(x) for x in extra_forbidden if _s(x))
    negative = ", ".join(dict.fromkeys(forbidden + ["texto renderizado", "logotipos inventados", "marca-d'água", "elementos deformados", "brilhos decorativos sem função"]))

    if transparent:
        background_prompt = "fundo genuinamente transparente em PNG, sem sombra de chão falsa e sem halo de recorte"
    else:
        background_prompt = background
    text_rule = "não incluir texto, letras, números, logotipo ou marca-d'água; o texto será adicionado separadamente e permanecerá editável no Canva" if no_text else "não inventar preços, provas, datas, disponibilidade ou alegações; qualquer texto precisa corresponder exatamente aos dados fornecidos"

    if transparent:
        cutout_layout = supplied_layout or "centralizado, isolado, sem cenário e sem necessidade de abrir espaço para texto dentro do objeto"
        composition_prompt = f"isolamento de recorte, objeto inteiro e sem partes cortadas, escala equilibrada ocupando cerca de 70–80% do quadro, margem transparente limpa; composição do recorte: {cutout_layout}"
    else:
        composition_prompt = f"composição: {layout}; mantenha área negativa limpa e útil para texto editável no formato {format_label}"
    image_prompt = (
        f"Crie um elemento visual comercial para {business_type}, para {goal}. "
        f"Foco único e específico: {subject}. Mostrar a ação/objeto de forma reconhecível para quem conhece esse serviço, sem colagem de ideias nem símbolo genérico. "
        f"Ambiente: {background_prompt}. Direção de arte: {style}. "
        f"{composition_prompt}. Enquadramento: {crop}. Ponto de vista/câmera: {camera}. "
        f"Iluminação: {light}. Paleta: {', '.join(palette)} ({palette_note}). "
        f"Texturas e realismo: {required_visual_details}. Formato final {format_label}, proporção {ratio} ({dimensions}). "
        f"Evite: {negative}. {text_rule}"
    )

    if headline:
        title_line = f"título principal exatamente: ‘{headline}’"
    else:
        title_line = "reservar uma área clara para uma manchete curta, editável no Canva; não inventar o texto da oferta"
    if offer:
        offer_line = f"oferta confirmada a comunicar: ‘{offer}’"
    else:
        offer_line = "não inventar preço, desconto, serviço, prazo ou benefício; deixar o campo de oferta vazio até verificar o que o negócio realmente vende"
    if supporting_copy:
        support_line = f"texto de apoio exatamente: ‘{supporting_copy}’"
    else:
        support_line = "usar no máximo uma linha de apoio editável apenas quando houver informação confirmada"
    if cta:
        cta_line = f"única chamada para ação: ‘{cta}’"
    else:
        cta_line = "reservar um botão/faixa de CTA editável, sem inventar link, telefone ou canal; selecionar o canal real após pesquisar o perfil"

    magic_design_prompt = (
        f"Crie uma peça comercial editável em Canva para {business_name or business_type}. "
        f"Objetivo: {goal}. Público: {business_type} local e seus clientes potenciais. "
        f"Formato final: {format_label}, {ratio}, {dimensions}. "
        f"Hierarquia visual: 1) {title_line}; 2) {offer_line}; 3) {support_line}; 4) {cta_line}. "
        f"Direção de arte: {style}. Paleta: {', '.join(palette)}. "
        f"Use um único foco visual principal baseado no elemento gerado em Magic Media, alinhamento consistente, margens generosas, contraste alto e espaço negativo útil. "
        f"Evite o layout genérico de template, excesso de ícones, brilhos, sombras, degradês e elementos sem função. "
        f"Não crie prova social, preços, descontos ou promessas. O texto deve ficar editável. "
        f"Se houver perfil ou referência real da marca, respeite sua identidade e não a substitua por uma estética genérica."
    )

    missing_facts = []
    if not business_name:
        missing_facts.append("nome oficial do negócio, caso precise aparecer na peça")
    if not brand_observed:
        missing_facts.append("identidade visual observada de verdade no perfil/site/arquivos da marca; uma URL sozinha não confirma cores nem estilo")
    if not offer:
        missing_facts.append("serviço/oferta real a divulgar")
    if not headline:
        missing_facts.append("mensagem principal aprovada/confirmada")
    if not cta:
        missing_facts.append("canal e chamada de ação confirmados")

    return {
        "status": "READY_FOR_ART_DIRECTION" if not missing_facts else "READY_WITH_FACTS_TO_VERIFY",
        "publish_ready": not missing_facts,
        "niche_id": niche["id"],
        "business": {"name": business_name or None, "category": business_type, "profile_url": brand_source or None},
        "brand_observation_status": "observed" if brand_observed else "not_observed_url_is_reference_only",
        "creative_strategy": {
            "goal": goal,
            "audience": _s(data.get("audience"), f"clientes potenciais de {business_type} que usam o celular para escolher e entrar em contato"),
            "offer": offer or None,
            "headline": headline or None,
            "supporting_copy": supporting_copy or None,
            "cta": cta or None,
            "single_primary_message": True,
            "palette": palette,
            "palette_basis": palette_note,
            "style": style,
            "format": {"key": fmt_key, "ratio": ratio, "dimensions": dimensions},
            "layout": layout,
        },
        "magic_media_element_prompt": image_prompt,
        "magic_design_layout_prompt": magic_design_prompt,
        "canva_workflow": [
            "Conferir o perfil/site/portfólio real do negócio e recolher referências de cor, tipografia, serviços e linguagem visual.",
            "Definir uma única meta e confirmar que serviço, preço, promoção, prazo e CTA são fatos reais.",
            "Abrir Apps > Magic Media (ou Magic Media no painel lateral) e gerar o elemento com o prompt completo; variar a composição se o primeiro resultado parecer genérico.",
            "Adicionar o elemento à página e compor a peça no Canva com texto editável, hierarquia, grid e espaço negativo. Não confiar em texto gerado dentro da imagem.",
            "Usar Magic Design como ponto de partida apenas se o texto e o briefing estiverem específicos; reestruturar qualquer layout que pareça um template genérico.",
            "Revisar em tamanho de celular, verificar erros visuais do elemento gerado, contraste, margens, recorte, ortografia, informações comerciais e formato de exportação.",
            "Salvar versão editável e exportar no formato exato da plataforma de destino."
        ],
        "quality_gate": design_policy["quality_gate"],
        "facts_to_verify_before_publish": missing_facts,
        "do_not_publish_without_factual_copy": bool(missing_facts),
    }
