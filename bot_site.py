import os, time, random, requests
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

# → Carrega variáveis de ambiente
load_dotenv()
OPENAI_KEY   = os.getenv("OPENROUTER_API_KEY")
NEWS_KEY     = os.getenv("NEWS_API_KEY")
AFILIADO     = os.getenv("AFILIADO")
NUM_NOTICIAS = int(os.getenv("NUM_NOTICIAS", 1))
NUM_PROD     = int(os.getenv("NUM_PROD", 1))

# → Paths
TEMPLATE_DIR = "templates"
OUTPUT_DIR   = "site"
POSTS_DIR    = os.path.join(OUTPUT_DIR, "posts")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

# — Busca títulos de notícias de hoje e ontem
def obter_temas_noticia(qtd=1):
    ontem = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    hoje = datetime.now().strftime('%Y-%m-%d')
    url = (
        f"https://newsapi.org/v2/everything?"
        f"from={ontem}&to={hoje}&sortBy=publishedAt&language=pt&"
        f"pageSize={qtd}&apiKey={NEWS_KEY}"
    )
    resp = requests.get(url).json()
    if resp.get("status") != "ok":
        return []
    return [a["title"] for a in resp["articles"] if a.get("title")]

# — Gera post via OpenRouter (GPT-3.5-turbo)
def gerar_artigo(titulo):
    prompt = (
        f"Crie um artigo informativo e formal sobre: '{titulo}'. "
        "Use subtítulos (<h3>), listas (<ul><li>), e finalize com um link de afiliado: "
        f"{AFILIADO}"
    )
    headers = {"Authorization": f"Bearer {OPENAI_KEY}"}
    body = {"model":"gpt-3.5-turbo","messages":[{"role":"user","content":prompt}]}
    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

# — Salva um post HTML via template
def salvar_post(title, content):
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    slug = "".join(c for c in title if c.isalnum() or c in "-_ ").strip().replace(" ", "-")[:50]
    filename = f"{date_str.replace(':','-')}_{slug}.html"
    tmpl = env.get_template("post.html")
    html  = tmpl.render(title=title, date=date_str, content=content)
    os.makedirs(POSTS_DIR, exist_ok=True)
    path = os.path.join(POSTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return {"title": title, "date": date_str, "filename": filename}

# — Atualiza index.html com lista de posts
def atualizar_index():
    posts = sorted(
        [f for f in os.listdir(POSTS_DIR) if f.endswith(".html")],
        reverse=True
    )
    data = []
    for fn in posts:
        # obtem title e date do filename
        parts = fn.split("_",1)
        date = parts[0].replace("-",":",1)
        title = fn.split("_",1)[1].rsplit(".",1)[0].replace("-", " ")
        data.append({"title": title, "date": date, "filename": fn})
    tmpl = env.get_template("index.html")
    html = tmpl.render(posts=data)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR,"index.html"),"w",encoding="utf-8") as f:
        f.write(html)

# — Fluxo 5-2-3-1
def ciclo():
    # 1 notícia atual
    titulos = obter_temas_noticia(NUM_NOTICIAS)
    for t in titulos:
        content = gerar_artigo(t)
        salvar_post(t, content)
    time.sleep(5*60)

    # 1 produto famoso (fallback de lista)
    produtos = ["Top 10 celulares 2025","Melhores fones wireless","Relógios smartwatch"]
    t = random.choice(produtos)
    c = gerar_artigo(t)
    salvar_post(t, c)
    time.sleep(5*60)

    # 2 posts diversos (qualquer tema)
    gerais = ["Guerras recentes no mundo", "Novas regras do futebol", "Tendências da moda 2025"]
    for t in random.sample(gerais,2):
        c = gerar_artigo(t)
        salvar_post(t, c)
    time.sleep(5*60)

    # 1 produto de novo
    t = random.choice(produtos)
    c = gerar_artigo(t)
    salvar_post(t, c)
    time.sleep(5*60)

if __name__=="__main__":
    while True:
        try:
            ciclo()
            atualizar_index()
            print("✅ Ciclo completo. Próximo em 5 minutos.")
        except Exception as e:
            print("❌ Erro:", e)
            time.sleep(5*60)
