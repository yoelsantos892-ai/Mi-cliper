import argparse, json, os, re, shutil, subprocess, urllib.parse, urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
MUSIC_URLS = [
    "https://freepd.com/music/3%20am%20West%20End.mp3",
    "https://freepd.com/music/Arpent.mp3",
]
RULES = [
    ("dinero", {"dinero","euros","euro","dolares","dólares","facturar","facturando","facture","facturé","facturo","facturó","millon","millón","millones","ingresos","beneficio","cobrar","pagar","billetes","banco","ganar","ganando","rentabilidad"}, ["counting money dark","gold watch luxury dark"], {"money","cash","dollar","euro","currency","gold","watch","finance","bank","wealth","coin","business"}),
    ("ecommerce", {"shopify","tienda","tiendas","ecommerce","dropshipping","producto","productos","anuncios","vender","vendiendo","ventas","clientes","pedidos","ordenador","portatil","portátil","web","marca"}, ["laptop dark office","typing laptop night"], {"laptop","computer","office","desk","typing","business","work","screen","technology","workspace","keyboard"}),
    ("logistica", {"china","fabrica","fábrica","fabricas","fábricas","almacen","almacén","envio","envío","envios","envíos","paquete","paquetes","proveedor","proveedores","importar","contenedor"}, ["warehouse logistics","cargo ship container"], {"warehouse","shipping","cargo","container","factory","logistics","port","box","delivery","truck","freight"}),
    ("lujo", {"coche","coches","auto","autos","lamborghini","porsche","ferrari","dubai","dubái","avion","avión","viajar","viajando","reloj","mansion","mansión","yate","hotel","libertad"}, ["sports car night","dubai night skyline"], {"car","supercar","luxury","dubai","skyline","city","night","jet","airplane","architecture","building"}),
    ("mentalidad", {"disciplina","mentalidad","miedo","madrugar","gimnasio","entrenar","habitos","hábitos","fracaso","estancado","esfuerzo","enfoque","constancia","riesgo","decision","decisión"}, ["man night city","gym dark workout"], {"city","night","gym","fitness","workout","training","walking","silhouette","running","street","focus"}),
]
BLOCKED = {"family","cry","crying","sad","sadness","tears","baby","child","kid","children","hospital","doctor","funeral","wedding","cartoon","animation","anime","dog","cat","pet","cow","farm","beach","party","dance","comedy","meme","kiss","flower","food","cooking"}
TAGS = {
    "marc_verdu": {
        "dinero": [["#marcverdu","#negociosonline","#facturacion","#emprendedores","#ecommerce"],["#marcverdu","#libertadfinanciera","#ganardinero","#negociosdigitales","#exito"]],
        "ecommerce": [["#marcverdu","#dropshipping","#ecommerce","#tiendaonline","#shopify"],["#marcverdu","#dropshippingespaña","#ventas","#marketingdigital","#emprender"]],
        "logistica": [["#marcverdu","#ecommerce","#importacion","#dropshipping","#negocios"],["#marcverdu","#china","#tiendaonline","#emprendimiento","#ventas"]],
        "lujo": [["#marcverdu","#lifestyle","#emprendimiento","#negocios","#motivacion"],["#marcverdu","#exito","#mentemillonaria","#libertad","#emprendedores"]],
        "mentalidad": [["#marcverdu","#mentalidad","#emprender","#desarrollopersonal","#disciplina"],["#marcverdu","#exito","#habitos","#emprendedores","#negocios"]],
    },
    "arz_urus": {
        "dinero": [["#arzurus","#negociosonline","#emprendedores","#ecommerce","#libertadfinanciera"],["#arzurus","#ganardinero","#negociosdigitales","#facturacion","#exito"]],
        "ecommerce": [["#arzurus","#ecommerce","#dropshipping","#tiendaonline","#ventas"],["#arzurus","#shopify","#marketingdigital","#emprendimiento","#negocios"]],
        "logistica": [["#arzurus","#ecommerce","#china","#negocios","#emprendedores"],["#arzurus","#dropshipping","#importacion","#tiendaonline","#ventas"]],
        "lujo": [["#arzurus","#lifestyle","#supercoches","#emprendimiento","#dubai"],["#arzurus","#lujo","#exito","#libertadfinanciera","#negocios"]],
        "mentalidad": [["#arzurus","#mentalidad","#disciplina","#emprender","#desarrollopersonal"],["#arzurus","#exito","#motivacion","#emprendedores","#habitos"]],
    },
    "ambos": {
        "dinero": [["#ecommerce","#negociosonline","#emprendedores","#libertadfinanciera","#dinero"],["#negociosdigitales","#facturacion","#emprendimiento","#exito","#ventas"]],
        "ecommerce": [["#dropshipping","#ecommerce","#shopify","#tiendaonline","#emprender"],["#ventas","#marketingdigital","#negociosonline","#emprendedores","#ecommerce"]],
        "logistica": [["#ecommerce","#china","#importacion","#negocios","#tiendaonline"],["#dropshipping","#proveedores","#emprendimiento","#ventas","#negocios"]],
        "lujo": [["#lifestyle","#emprendimiento","#exito","#negocios","#libertadfinanciera"],["#lujo","#motivacion","#emprendedores","#mentemillonaria","#negocios"]],
        "mentalidad": [["#mentalidad","#disciplina","#desarrollopersonal","#emprender","#exito"],["#habitos","#emprendedores","#motivacion","#negocios","#crecimientopersonal"]],
    },
}

def probe(p):
    out = subprocess.check_output(["ffprobe","-v","error","-show_entries","stream=width,height:format=duration","-of","json",str(p)], text=True)
    d = json.loads(out)
    w, h = next(((int(s["width"]), int(s["height"])) for s in d.get("streams",[]) if "width" in s), (1280,720))
    return w, h, float(d.get("format",{}).get("duration", 40.0))

def dl(url, dst):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=25) as r, open(dst, "wb") as f:
        shutil.copyfileobj(r, f)

def pre_split(inp, out):
    w, h, _ = probe(inp)
    if w <= h:
        shutil.copyfile(inp, out); return
    hw = (w // 2) // 2 * 2
    ch = min(h, (int(hw * 638 / 720) // 2) * 2)
    cy = max(0, int((h - ch) * 0.25))
    fc = f"[0:v]crop={hw}:{ch}:0:{cy},scale=720:638:flags=lanczos,setsar=1,pad=720:642:0:0:black[t];[0:v]crop={hw}:{ch}:{w-hw}:{cy},scale=720:638:flags=lanczos,setsar=1[b];[t][b]vstack[v]"
    subprocess.run(["ffmpeg","-y","-i",str(inp),"-filter_complex",fc,"-map","[v]","-map","0:a?","-c:v","libx264","-preset","veryfast","-crf","20","-c:a","copy",str(out)], check=True)

def get_music(custom_url):
    cdir = Path.home()/".cache"/"micliper_music"; cdir.mkdir(parents=True, exist_ok=True)
    if custom_url:
        cp = cdir/"custom_bg.mp3"
        try:
            if custom_url.lower().endswith(".mp3"): dl(custom_url, cp)
            else: subprocess.run(["yt-dlp","-x","--audio-format","mp3","--no-playlist","-o",str(cp),custom_url], check=True)
            if cp.exists() and cp.stat().st_size > 20000: return cp
        except Exception as e: print(f"Musica custom fallo: {e}")
    dp = cdir/"dark_ambient.mp3"
    if dp.exists() and dp.stat().st_size > 20000: return dp
    for u in MUSIC_URLS:
        try:
            dl(u, dp)
            if dp.exists() and dp.stat().st_size > 20000: return dp
        except Exception as e: print(f"Error musica {u}: {e}")
    return None

def get_broll(topic, key, cdir, used):
    rule = next((r for r in RULES if r[0] == topic), None)
    if not key or not rule: return None
    for q in rule[2]:
        try:
            u = f"https://pixabay.com/api/videos/?{urllib.parse.urlencode({'key':key,'q':q,'video_type':'film','safesearch':'true','per_page':15,'min_width':720})}"
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=15) as r:
                hits = json.loads(r.read().decode("utf-8")).get("hits", [])
        except Exception: continue
        for h in hits:
            vid = h.get("id")
            if vid in used or not (3 <= h.get("duration",0) <= 60): continue
            tags = {t.strip().lower() for t in h.get("tags","").split(",") if t.strip()}
            if (tags & BLOCKED) or not (tags & rule[3]): continue
            vinfo = h.get("videos",{}).get("medium") or h.get("videos",{}).get("small") or {}
            if not vinfo.get("url"): continue
            fp = cdir/f"broll_{vid}.mp4"
            try:
                if not fp.exists(): dl(vinfo["url"], fp)
                if fp.exists() and fp.stat().st_size > 30000:
                    used.add(vid); return fp
            except Exception: continue
    return None

def make_copy(n, text, dur, creador, score, n_broll):
    nombre = {"marc_verdu":"Marc Verdú","arz_urus":"ARZ Urus"}.get(creador, "Emprendimiento Real")
    toks = re.findall(r"[a-záéíóúüñ]+", text.lower())
    topic = max(RULES, key=lambda r: sum(1 for t in toks if t in r[1]))[0]
    if sum(1 for t in toks if t in next(r[1] for r in RULES if r[0]==topic)) == 0:
        topic = "ecommerce" if ({"shopify","tienda","vender"} & set(toks)) else "mentalidad"
    nums = [m.strip() for m in re.findall(r"\b\d+(?:[.,]\d+)?\s*(?:mil|millones|millón|euros|euro|€|dólares|dolares|\$|%|años|meses|días|horas)?\b", text, re.I) if len(m.strip())>=2]
    num = nums[0] if nums else ""
    first = re.split(r"[.!?]", text)[0].strip() if text else ""
    prev = (first[:85]+"...") if len(first)>88 else first
    bank = {
        "dinero": (f"De 0 a {num}" if num else "La verdad sobre facturar", [f"Con {num}: lo que nadie cuenta antes de llegar ahi" if num else "La parte del dinero que casi nadie te ensena","Por que la mayoria gana menos por no entender esto",f"{nombre} explica donde cambian los ingresos"],"¿Crees que hoy cualquiera puede lograr estas cifras o falta contexto detras? Te leo abajo."),
        "ecommerce": ("El error en tu tienda" if ("error" in text.lower() or "no " in text.lower()) else "Asi se vende en 2026", ["Si tu tienda online no despega, mira esto antes de cerrar","El fallo silencioso que quema tu presupuesto en anuncios",f"Como enfoca las ventas {nombre} sin complicarse"],"¿Sigue siendo rentable empezar una tienda asi este año o ya esta saturado? Opina."),
        "logistica": ("Asi negocian en China", ["Lo que pasa de verdad cuando compras directo a fabrica","El detalle de los envios que separa a un aficionado de una marca",f"Detras de escena: como mueve productos {nombre}"],"¿Te atreverias a negociar directo con proveedores o prefieres empezar sin stock?"),
        "lujo": ("El precio de esta vida", ["Todos quieren el coche y los viajes, pocos aguantan este proceso","Lo que realmente te da el dinero cuando pasas la meta",f"{nombre}: por que el estilo de vida es la consecuencia, no el inicio"],"¿Suerte, contactos o sacrificio real? Quiero leer opiniones sinceras."),
        "mentalidad": (f"Si tienes {num}" if num else "El golpe de realidad", ["La regla incomoda que te desbloquea cuando estas estancado","Escucha esto si sientes que trabajas mucho y avanzas lento",f"El cambio de chip que defiende {nombre}"],"¿Estas de acuerdo con esta mentalidad o crees que exagera? Dime que piensas."),
    }
    scr, titles, deb = bank[topic]
    pool = TAGS.get(creador, TAGS["ambos"])[topic]
    t5 = pool[(n - 1) % len(pool)]
    return f"""================ VIDEO: {n:02d}_clip.mp4 ================
Duracion: {dur:.1f}s | Tema: {topic.upper()} | Nota: {score} | B-Roll: {n_broll} tomas
Arranca diciendo: "{prev or '(Sin texto)'}"
-> TITULO EN PANTALLA: {scr[:38]}
-> TITULOS:
   1) {titles[0]}
   2) {titles[1]}
   3) {titles[2]}
-> COPIAR EN TIKTOK / INSTAGRAM REELS:
{titles[0]} {deb}
{' '.join(t5)}
-> COPIAR EN FACEBOOK REELS:
{titles[1]} {deb}
{' '.join(t5[:3])}
--------------------------------------------------------------\n"""

def post(args):
    from faster_whisper import WhisperModel
    clips = sorted(Path("output").glob("clip_*.mp4")) or sorted(Path("ai-agent-cut/output").glob("clip_*.mp4"))
    if not clips: raise RuntimeError("No se encontraron clips en output/")
    fdir = Path("final_output"); fdir.mkdir(parents=True, exist_ok=True)
    bdir = Path("broll_cache"); bdir.mkdir(parents=True, exist_ok=True)
    key = os.environ.get("PIXABAY_API_KEY","").strip()
    music = get_music(args.url_musica.strip()) if args.musica == "si" else None
    wm = WhisperModel(args.modelo, device="cpu", compute_type="int8")
    rp = Path("output/report.json")
    scores = {}
    if rp.exists():
        try:
            d = json.loads(rp.read_text(encoding="utf-8"))
            for i, it in enumerate(d if isinstance(d,list) else d.get("clips",[]), 1):
                if isinstance(it, dict): scores[i] = it.get("score","-")
        except Exception: pass
    used, blocks = set(), ["GUIA EXACTA PARA PUBLICAR (EMPAREJADA POR NUMERO DE CLIP)\n"]
    for i, cp in enumerate(clips, 1):
        outp = fdir/f"{i:02d}_clip.mp4"
        _, _, dur = probe(cp)
        segs, _ = wm.transcribe(str(cp), language="es", word_timestamps=True, vad_filter=True)
        words, texts = [], []
        for s in segs:
            texts.append(s.text.strip())
            for w in (s.words or []): words.append((w.word.strip(), float(w.start)))
        full_txt = " ".join(t for t in texts if t).strip()
        inserts = []
        if args.broll == "si" and key:
            used_tp, last_t = set(), -99.0
            for wtxt, wt in words:
                if wt < 5.0 or wt > max(6.0, dur-4.0) or wt - last_t < 10.5: continue
                cw = re.sub(r"[^\wáéíóúüñ]", "", wtxt.lower())
                for tp, trigs, _, _ in RULES:
                    if tp not in used_tp and cw in trigs:
                        bf = get_broll(tp, key, bdir, used)
                        if bf: inserts.append((wt, bf)); used_tp.add(tp); last_t = wt
                        break
                if len(inserts) >= 2: break
        kbps = min(1250, max(450, int((4.65 * 8 * 1024) / max(dur, 10.0) - 96)))
        cmd = ["ffmpeg","-y","-i",str(cp)]
        fp, cv, idx = [], "[0:v]", 1
        for k, (ts, bp) in enumerate(inserts):
            cmd += ["-i", str(bp)]
            te = min(dur-0.5, ts+2.3); bl = max(1.0, te-ts); fo = max(0.3, bl-0.25)
            fp.append(f"[{idx}:v]trim=0:{bl:.2f},setpts=PTS-STARTPTS,scale=720:820:force_original_aspect_ratio=increase,crop=720:820,setsar=1,format=yuva420p,fade=t=in:st=0:d=0.25:alpha=1,fade=t=out:st={fo:.2f}:d=0.25:alpha=1,setpts=PTS-STARTPTS+{ts:.2f}/TB[b{k}]")
            fp.append(f"{cv}[b{k}]overlay=0:0:eof_action=pass:enable='between(t,{ts:.2f},{te:.2f})'[v{k}]")
            cv = f"[v{k}]"; idx += 1
        if args.musica == "si" and music:
            cmd += ["-stream_loop","-1","-i",str(music)]
            fp += ["[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[va]", f"[{idx}:a]lowpass=f=3200,volume=0.085[ma]", "[va][ma]amix=inputs=2:duration=first:dropout_transition=2[ao]"]
        else:
            fp += ["[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[ao]"]
        if cv == "[0:v]": fp.insert(0, "[0:v]null[vp]"); cv = "[vp]"
        cmd += ["-filter_complex",";".join(fp),"-map",cv,"-map","[ao]","-c:v","libx264","-preset","medium","-b:v",f"{kbps}k","-maxrate",f"{int(kbps*1.2)}k","-bufsize",f"{kbps*2}k","-c:a","aac","-b:a","96k","-movflags","+faststart",str(outp)]
        subprocess.run(cmd, check=True)
        print(f"Generado: {outp}")
        blocks.append(make_copy(i, full_txt, dur, args.creador, scores.get(i,"-"), len(inserts)))
    (fdir/"00_LEER_TITULOS_Y_HASHTAGS.txt").write_text("\n".join(blocks), encoding="utf-8")
    print("Proceso completado en final_output/")

if __name__ == "__main__":
    p = argparse.ArgumentParser(); s = p.add_subparsers(dest="cmd", required=True)
    p1 = s.add_parser("pre-split"); p1.add_argument("--input", required=True); p1.add_argument("--output", required=True)
    p2 = s.add_parser("post"); p2.add_argument("--creador", default="marc_verdu"); p2.add_argument("--broll", default="no"); p2.add_argument("--musica", default="si"); p2.add_argument("--url-musica", default=""); p2.add_argument("--modelo", default="small")
    a = p.parse_args()
    pre_split(a.input, a.output) if a.cmd == "pre-split" else post(a)
# FIN_COMPLETO
