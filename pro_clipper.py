import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

MUSIC_SOURCES = [
    "https://freepd.com/music/3%20am%20West%20End.mp3",
    "https://freepd.com/music/Arpent.mp3",
    "https://freepd.com/music/Limit%2070.mp3",
]

BROLL_RULES = [
    {
        "topic": "dinero",
        "triggers": {
            "dinero", "euros", "euro", "dolares", "dólares", "facturar", "facturando",
            "facture", "facturé", "facturo", "facturó", "millon", "millón", "millones",
            "ingresos", "beneficio", "beneficios", "cobrar", "pagar", "billetes", "banco",
            "ganar", "ganando", "rentabilidad", "margen", "capital",
        },
        "queries": ["counting money dark", "gold watch luxury dark"],
        "required_tags": {"money", "cash", "dollar", "euro", "currency", "gold", "watch", "finance", "bank", "wealth", "coin", "business"},
    },
    {
        "topic": "ecommerce",
        "triggers": {
            "shopify", "tienda", "tiendas", "ecommerce", "dropshipping", "producto",
            "productos", "anuncios", "vender", "vendiendo", "ventas", "clientes",
            "pedidos", "ordenador", "portatil", "portátil", "web", "marca", "trafico", "tráfico",
        },
        "queries": ["laptop dark office", "typing laptop night"],
        "required_tags": {"laptop", "computer", "office", "desk", "typing", "business", "work", "screen", "technology", "workspace", "keyboard"},
    },
    {
        "topic": "logistica",
        "triggers": {
            "china", "fabrica", "fábrica", "fabricas", "fábricas", "almacen", "almacén",
            "envio", "envío", "envios", "envíos", "paquete", "paquetes", "proveedor",
            "proveedores", "importar", "contenedor", "mercancia", "mercancía",
        },
        "queries": ["warehouse logistics", "cargo ship container"],
        "required_tags": {"warehouse", "shipping", "cargo", "container", "factory", "logistics", "port", "box", "delivery", "truck", "freight"},
    },
    {
        "topic": "lujo",
        "triggers": {
            "coche", "coches", "auto", "autos", "lamborghini", "porsche", "ferrari",
            "dubai", "dubái", "avion", "avión", "viajar", "viajando", "reloj",
            "mansion", "mansión", "yate", "hotel", "libertad",
        },
        "queries": ["sports car night", "dubai night skyline"],
        "required_tags": {"car", "supercar", "luxury", "dubai", "skyline", "city", "night", "jet", "airplane", "architecture", "building"},
    },
    {
        "topic": "mentalidad",
        "triggers": {
            "disciplina", "mentalidad", "miedo", "madrugar", "gimnasio", "entrenar",
            "habitos", "hábitos", "fracaso", "estancado", "esfuerzo", "enfoque",
            "constancia", "riesgo", "decisión", "decision",
        },
        "queries": ["man night city", "gym dark workout"],
        "required_tags": {"city", "night", "gym", "fitness", "workout", "training", "walking", "silhouette", "running", "street", "focus"},
    },
]

BLOCKED_TAGS = {
    "family", "cry", "crying", "sad", "sadness", "tears", "baby", "child", "kid",
    "children", "hospital", "doctor", "funeral", "wedding", "cartoon", "animation",
    "anime", "dog", "cat", "pet", "cow", "farm", "beach", "party", "dance",
    "comedy", "meme", "kiss", "flower", "food", "cooking",
}

HASHTAG_POOLS = {
    "marc_verdu": {
        "dinero": [
            ["#marcverdu", "#negociosonline", "#facturacion", "#emprendedores", "#ecommerce"],
            ["#marcverdu", "#libertadfinanciera", "#ganardinero", "#negociosdigitales", "#exito"],
        ],
        "ecommerce": [
            ["#marcverdu", "#dropshipping", "#ecommerce", "#tiendaonline", "#shopify"],
            ["#marcverdu", "#dropshippingespaña", "#ventas", "#marketingdigital", "#emprender"],
        ],
        "logistica": [
            ["#marcverdu", "#ecommerce", "#importacion", "#dropshipping", "#negocios"],
            ["#marcverdu", "#china", "#tiendaonline", "#emprendimiento", "#ventas"],
        ],
        "lujo": [
            ["#marcverdu", "#lifestyle", "#emprendimiento", "#negocios", "#motivacion"],
            ["#marcverdu", "#exito", "#mentemillonaria", "#libertad", "#emprendedores"],
        ],
        "mentalidad": [
            ["#marcverdu", "#mentalidad", "#emprender", "#desarrollopersonal", "#disciplina"],
            ["#marcverdu", "#exito", "#habitos", "#emprendedores", "#negocios"],
        ],
    },
    "arz_urus": {
        "dinero": [
            ["#arzurus", "#negociosonline", "#emprendedores", "#ecommerce", "#libertadfinanciera"],
            ["#arzurus", "#ganardinero", "#negociosdigitales", "#facturacion", "#exito"],
        ],
        "ecommerce": [
            ["#arzurus", "#ecommerce", "#dropshipping", "#tiendaonline", "#ventas"],
            ["#arzurus", "#shopify", "#marketingdigital", "#emprendimiento", "#negocios"],
        ],
        "logistica": [
            ["#arzurus", "#ecommerce", "#china", "#negocios", "#emprendedores"],
            ["#arzurus", "#dropshipping", "#importacion", "#tiendaonline", "#ventas"],
        ],
        "lujo": [
            ["#arzurus", "#lifestyle", "#supercoches", "#emprendimiento", "#dubai"],
            ["#arzurus", "#lujo", "#exito", "#libertadfinanciera", "#negocios"],
        ],
        "mentalidad": [
            ["#arzurus", "#mentalidad", "#disciplina", "#emprender", "#desarrollopersonal"],
            ["#arzurus", "#exito", "#motivacion", "#emprendedores", "#habitos"],
        ],
    },
    "ambos": {
        "dinero": [
            ["#ecommerce", "#negociosonline", "#emprendedores", "#libertadfinanciera", "#dinero"],
            ["#negociosdigitales", "#facturacion", "#emprendimiento", "#exito", "#ventas"],
        ],
        "ecommerce": [
            ["#dropshipping", "#ecommerce", "#shopify", "#tiendaonline", "#emprender"],
            ["#ventas", "#marketingdigital", "#negociosonline", "#emprendedores", "#ecommerce"],
        ],
        "logistica": [
            ["#ecommerce", "#china", "#importacion", "#negocios", "#tiendaonline"],
            ["#dropshipping", "#proveedores", "#emprendimiento", "#ventas", "#negocios"],
        ],
        "lujo": [
            ["#lifestyle", "#emprendimiento", "#exito", "#negocios", "#libertadfinanciera"],
            ["#lujo", "#motivacion", "#emprendedores", "#mentemillonaria", "#negocios"],
        ],
        "mentalidad": [
            ["#mentalidad", "#disciplina", "#desarrollopersonal", "#emprender", "#exito"],
            ["#habitos", "#emprendedores", "#motivacion", "#negocios", "#crecimientopersonal"],
        ],
    },
}


def run_cmd(cmd):
    subprocess.run(cmd, check=True)


def probe_video(path):
    out = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-show_entries",
            "stream=width,height:format=duration", "-of", "json", str(path)
        ],
        text=True,
    )
    info = json.loads(out)
    w, h = 1280, 720
    for s in info.get("streams", []):
        if "width" in s and "height" in s:
            w, h = int(s["width"]), int(s["height"])
            break
    dur = float(info.get("format", {}).get("duration", 40.0))
    return w, h, dur


def pre_split(input_path, output_path):
    w, h, _ = probe_video(input_path)
    if w <= h:
        shutil.copyfile(input_path, output_path)
        return
    half_w = (w // 2) // 2 * 2
    crop_h = min(h, (int(half_w * 638 / 720) // 2) * 2)
    crop_y = max(0, int((h - crop_h) * 0.25))
    fc = (
        f"[0:v]crop={half_w}:{crop_h}:0:{crop_y},scale=720:638:flags=lanczos,setsar=1,pad=720:642:0:0:black[top];"
        f"[0:v]crop={half_w}:{crop_h}:{w - half_w}:{crop_y},scale=720:638:flags=lanczos,setsar=1[bot];"
        f"[top][bot]vstack[v]"
    )
    run_cmd([
        "ffmpeg", "-y", "-i", str(input_path),
        "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "copy",
        str(output_path),
    ])


def download_file(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as resp, open(dest, "wb") as f:
        shutil.copyfileobj(resp, f)


def get_music_track(custom_url):
    cache_dir = Path.home() / ".cache" / "micliper_music"
    cache_dir.mkdir(parents=True, exist_ok=True)
    if custom_url:
        custom_path = cache_dir / "custom_bg.mp3"
        try:
            if custom_url.lower().endswith(".mp3"):
                download_file(custom_url, custom_path)
            else:
                run_cmd([
                    "yt-dlp", "-x", "--audio-format", "mp3", "--no-playlist",
                    "-o", str(custom_path), custom_url
                ])
            if custom_path.exists() and custom_path.stat().st_size > 20000:
                return custom_path
        except Exception as exc:
            print(f"Aviso musica personalizada no disponible ({exc}); usando respaldo.")

    default_path = cache_dir / "dark_ambient.mp3"
    if default_path.exists() and default_path.stat().st_size > 20000:
        return default_path

    for url in MUSIC_SOURCES:
        try:
            download_file(url, default_path)
            if default_path.exists() and default_path.stat().st_size > 20000:
                return default_path
        except Exception as exc:
            print(f"No se pudo descargar {url}: {exc}")
    return None


def fetch_pixabay_broll(topic, api_key, cache_dir, used_ids):
    if not api_key:
        return None
    rule = next((r for r in BROLL_RULES if r["topic"] == topic), None)
    if not rule:
        return None

    for query in rule["queries"]:
        params = urllib.parse.urlencode({
            "key": api_key,
            "q": query,
            "video_type": "film",
            "safesearch": "true",
            "per_page": 15,
            "min_width": 720,
        })
        api_url = f"https://pixabay.com/api/videos/?{params}"
        try:
            req = urllib.request.Request(api_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            print(f"Aviso Pixabay ({query}): {exc}")
            continue

        for hit in data.get("hits", []):
            vid_id = hit.get("id")
            if vid_id in used_ids:
                continue
            dur = hit.get("duration", 0)
            if dur < 3 or dur > 60:
                continue
            raw_tags = {t.strip().lower() for t in hit.get("tags", "").split(",") if t.strip()}
            if raw_tags & BLOCKED_TAGS:
                continue
            if not (raw_tags & rule["required_tags"]):
                continue
            videos = hit.get("videos", {})
            chosen = videos.get("medium") or videos.get("small")
            if not chosen or not chosen.get("url"):
                continue
            out_file = cache_dir / f"broll_{vid_id}.mp4"
            if not out_file.exists():
                try:
                    download_file(chosen["url"], out_file)
                except Exception:
                    continue
            if out_file.exists() and out_file.stat().st_size > 30000:
                used_ids.add(vid_id)
                return out_file
    return None


def transcribe_clip(clip_path, model):
    segments, _ = model.transcribe(
        str(clip_path), language="es", word_timestamps=True, vad_filter=True
    )
    words = []
    texts = []
    for seg in segments:
        texts.append(seg.text.strip())
        if seg.words:
            for w in seg.words:
                words.append({"word": w.word.strip(), "start": float(w.start), "end": float(w.end)})
    full_text = " ".join(t for t in texts if t).strip()
    return full_text, words


def detect_broll_spots(words, duration):
    spots = []
    used_topics = set()
    last_time = -99.0
    for w in words:
        t = w["start"]
        if t < 5.0 or t > max(6.0, duration - 4.0):
            continue
        if t - last_time < 10.5:
            continue
        clean = re.sub(r"[^\wáéíóúüñ]", "", w["word"].lower())
        for rule in BROLL_RULES:
            if rule["topic"] in used_topics:
                continue
            if clean in rule["triggers"]:
                spots.append((t, rule["topic"], clean))
                used_topics.add(rule["topic"])
                last_time = t
                break
        if len(spots) >= 2:
            break
    return spots


def detect_main_topic(text):
    tokens = re.findall(r"[a-záéíóúüñ]+", text.lower())
    token_set = set(tokens)
    best_topic = "mentalidad"
    best_hits = 0
    for rule in BROLL_RULES:
        hits = sum(1 for tok in tokens if tok in rule["triggers"])
        if hits > best_hits:
            best_hits = hits
            best_topic = rule["topic"]
    if best_hits == 0 and ({"shopify", "tienda", "vender"} & token_set):
        return "ecommerce"
    return best_topic


def extract_numbers(text):
    matches = re.findall(
        r"\b\d+(?:[.,]\d+)?\s*(?:mil|millones|millón|euros|euro|€|dólares|dolares|\$|%|años|meses|días|horas)?\b",
        text, flags=re.IGNORECASE
    )
    clean = [m.strip() for m in matches if len(m.strip()) >= 2]
    return clean[:2]


def build_viral_copy(clip_num, text, duration, creador, score):
    creador_nombre = {
        "marc_verdu": "Marc Verdú",
        "arz_urus": "ARZ Urus",
        "ambos": "Emprendimiento Real",
    }.get(creador, "Marc Verdú")

    topic = detect_main_topic(text)
    nums = extract_numbers(text)
    first_sentence = re.split(r"[.!?]", text)[0].strip() if text else ""
    preview = (first_sentence[:85] + "...") if len(first_sentence) > 88 else first_sentence

    num_txt = nums[0] if nums else ""

    if topic == "dinero":
        on_screen = f"De 0 a {num_txt}" if num_txt else "La verdad sobre facturar"
        titles = [
            f"Con {num_txt}: lo que nadie cuenta antes de llegar ahí" if num_txt else "La parte del dinero que casi nadie te enseña",
            "Por qué la mayoría gana menos por no entender esto",
            f"{creador_nombre} explica el punto exacto donde cambian los ingresos",
        ]
        debate = "¿Crees que hoy cualquiera puede lograr estas cifras o falta contexto detrás? Te leo abajo."
    elif topic == "ecommerce":
        on_screen = "El error en tu tienda" if "error" in text.lower() or "no" in text.lower() else "Así se vende en 2026"
        titles = [
            "Si tu tienda online no despega, mira esto antes de cerrar",
            "El fallo silencioso que quema tu presupuesto en anuncios",
            f"Cómo enfoca las ventas {creador_nombre} sin complicarse",
        ]
        debate = "¿Sigue siendo rentable empezar una tienda así este año o ya está saturado? Opina."
    elif topic == "logistica":
        on_screen = "Así negocian en China"
        titles = [
            "Lo que pasa de verdad cuando compras directo a fábrica",
            "El detalle de los envíos que separa a un aficionado de una marca",
            f"Detrás de escena: cómo mueve productos {creador_nombre}",
        ]
        debate = "¿Te atreverías a negociar directo con proveedores o prefieres empezar sin stock?"
    elif topic == "lujo":
        on_screen = "El precio de esta vida"
        titles = [
            "Todos quieren el coche y los viajes, pocos aguantan este proceso",
            "Lo que realmente te da el dinero cuando pasas la meta",
            f"{creador_nombre}: por qué el estilo de vida es la consecuencia, no el inicio",
        ]
        debate = "¿Suerte, contactos o sacrificio real? Quiero leer opiniones sinceras."
    else:
        on_screen = f"Si tienes {num_txt}" if num_txt else "El golpe de realidad"
        titles = [
            "La regla incómoda que te desbloquea cuando estás estancado",
            "Escucha esto si sientes que trabajas mucho y avanzas lento",
            f"El cambio de chip que defiende {creador_nombre}",
        ]
        debate = "¿Estás de acuerdo con esta mentalidad o crees que exagera? Dime qué piensas."

    pool = HASHTAG_POOLS.get(creador, HASHTAG_POOLS["ambos"]).get(topic, HASHTAG_POOLS["ambos"]["mentalidad"])
    tags_5 = pool[(clip_num - 1) % len(pool)]
    tags_fb = tags_5[:3]

    return {
        "clip_file": f"{clip_num:02d}_clip.mp4",
        "topic": topic,
        "duration": round(duration, 1),
        "score": score,
        "preview": preview or "(Sin texto detectado)",
        "on_screen": on_screen[:38],
        "titles": titles,
        "debate": debate,
        "tags_tt_ig": " ".join(tags_5),
        "tags_fb": " ".join(tags_fb),
    }


def render_final_clip(src_clip, out_clip, broll_inserts, music_path, use_music):
    _, _, dur = probe_video(src_clip)
    target_kbps = min(1250, max(450, int((4.65 * 8 * 1024) / max(dur, 10.0) - 96)))

    cmd = ["ffmpeg", "-y", "-i", str(src_clip)]
    inputs_idx = 1
    filter_parts = []
    cur_v = "[0:v]"

    for idx, (t_start, broll_path) in enumerate(broll_inserts):
        cmd.extend(["-i", str(broll_path)])
        b_idx = inputs_idx
        inputs_idx += 1
        b_label = f"[b{idx}]"
        out_label = f"[v{idx}]"
        t_end = min(dur - 0.5, t_start + 2.3)
        b_len = max(1.0, t_end - t_start)
        fade_out = max(0.3, b_len - 0.25)
        filter_parts.append(
            f"[{b_idx}:v]trim=0:{b_len:.2f},setpts=PTS-STARTPTS,"
            f"scale=720:820:force_original_aspect_ratio=increase,crop=720:820,setsar=1,"
            f"format=yuva420p,fade=t=in:st=0:d=0.25:alpha=1,fade=t=out:st={fade_out:.2f}:d=0.25:alpha=1,"
            f"setpts=PTS-STARTPTS+{t_start:.2f}/TB{b_label}"
        )
        filter_parts.append(
            f"{cur_v}{b_label}overlay=0:0:eof_action=pass:enable='between(t,{t_start:.2f},{t_end:.2f})'{out_label}"
        )
        cur_v = out_label

    if use_music and music_path is not None:
        cmd.extend(["-stream_loop", "-1", "-i", str(music_path)])
        m_idx = inputs_idx
        filter_parts.append("[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[voice]")
        filter_parts.append(f"[{m_idx}:a]lowpass=f=3200,volume=0.085[bgm]")
        filter_parts.append("[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]")
        audio_map = "[aout]"
    else:
        filter_parts.append("[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
        audio_map = "[aout]"

    if cur_v != "[0:v]":
        video_map = cur_v
    else:
        filter_parts.insert(0, "[0:v]null[vpass]")
        video_map = "[vpass]"

    cmd.extend([
        "-filter_complex", ";".join(filter_parts),
        "-map", video_map, "-map", audio_map,
        "-c:v", "libx264", "-preset", "medium",
        "-b:v", f"{target_kbps}k", "-maxrate", f"{int(target_kbps * 1.2)}k",
        "-bufsize", f"{target_kbps * 2}k",
        "-c:a", "aac", "-b:a", "96k",
        "-movflags", "+faststart",
        str(out_clip),
    ])
    run_cmd(cmd)


def load_scores():
    scores = {}
    rp = Path("output") / "report.json"
    if not rp.exists():
        return scores
    try:
        data = json.loads(rp.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("clips", [])
        for idx, item in enumerate(items, start=1):
            if isinstance(item, dict):
                scores[idx] = item.get("score", "-")
    except Exception:
        pass
    return scores


def post_process(args):
    from faster_whisper import WhisperModel

    raw_clips = sorted(Path("output").glob("clip_*.mp4"))
    if not raw_clips:
        raise RuntimeError("No se encontraron clips generados en output/")

    final_dir = Path("final_output")
    final_dir.mkdir(parents=True, exist_ok=True)
    broll_cache = Path("broll_cache")
    broll_cache.mkdir(parents=True, exist_ok=True)

    api_key = os.environ
