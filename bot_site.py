import os
import time
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime, timedelta
import random

# Carrega a chave da OpenRouter
load_dotenv()
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

def gerar_tema():
    print("Gerando tema...")
    ontem = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    hoje = datetime.utcnow().strftime("%Y-%m-%d")

    prompt = f"""
Crie um título criativo e direto para um post de afiliados. Use algum tema relevante baseado em alguma novidade que surgiu nos dias {ontem} ou {hoje}, dentro das áreas de tecnologia, casa, moda ou esportes.
Responda apenas com o título, nada mais.
"""
    resposta = client.chat.completions.create(
        model="openchat/openchat-7b",
        messages=[{"role": "user", "content": prompt}]
    )
    return resposta.choices[0].message.content.strip().replace('"', "")

def gerar_conteudo(titulo):
    print("Gerando conteúdo...")
    prompt = f"""
Crie um post de blog detalhado e envolvente com base neste título: "{titulo}". Escreva um artigo com pelo menos 4 parágrafos, explique bem o tema, com linguagem simples e natural. No final, recomende algum produto relacionado e inclua este link de afiliado:
https://www.amazon.com.br/?tag=autogadgetbr-20
"""
    resposta = client.chat.completions.create(
        model="openchat/openchat-7b",
        messages=[{"role": "user", "content": prompt}]
    )
    return resposta.choices[0].message.content.strip()

def salvar_post(titulo, conteudo):
    print("Salvando post...")
    data = datetime.now().strftime("%Y-%m-%d")
    nome_arquivo = f"{data}-{random.randint(1000,9999)}.html"
    caminho_post = os.path.join("site", "posts", nome_arquivo)

    # Garante que o diretório "posts" existe
    os.makedirs(os.path.join("site", "posts"), exist_ok=True)

    with open("site/templates/post.html", "r", encoding="utf-8") as modelo:
        html_base = modelo.read()
        html_pronto = html_base.replace("{{ titulo }}", titulo).replace("{{ conteudo }}", conteudo)

    with open(caminho_post, "w", encoding="utf-8") as arquivo:
        arquivo.write(html_pronto)

    print(f"Post salvo em: site/posts/{nome_arquivo}")

def main():
    titulo = gerar_tema()
    conteudo = gerar_conteudo(titulo)
    salvar_post(titulo, conteudo)

if __name__ == "__main__":
    while True:
        main()
        print("Aguardando 2 minutos...\n")
        time.sleep(120)
