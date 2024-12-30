import asyncio
from fastapi import FastAPI, HTTPException
from youtube_community_tab.helpers.utils import parse_count_text, safely_get_value_from_key
from youtube_community_tab.post import Post
from youtube_community_tab.community_tab import CommunityTab

app = FastAPI()


# --- RUTA PRINCIPAL ---
@app.get("/", tags=["General"])
def read_root():
    return {"message": "Bienvenido a la API de la pestaña de comunidad de YouTube"}

# --- RUTAS DE POSTS ---
@app.get("/find-all-posts/{channel_name}", tags=["Posts"])
async def get_posts(channel_name: str):
    try:
        community_tab = CommunityTab(f'@{channel_name}')
        await asyncio.to_thread(community_tab.load_posts)  # Ejecutar en un subproceso si es bloqueante
        if not community_tab.posts:
            raise HTTPException(status_code=404, detail="No se encontraron publicaciones para este canal")

        # Función para procesar cada post de manera concurrente
        async def process_post(post):
            post_data = post.as_json()

            # Obtener estadísticas (likes y comments) de manera asíncrona
            post_stats = await asyncio.to_thread(get_post_stats, post_data["post_id"])

            # Extraer datos requeridos
            author_name = safely_get_value_from_key(
                post_data, "author", "authorText", "runs", 0, "text", default="Desconocido"
            )
            
            thumbnails = safely_get_value_from_key(
                post_data, "backstage_attachment", "backstageImageRenderer", "image", "thumbnails", -1, "url", default="Desconocido"
            )

            content_runs = safely_get_value_from_key(post_data, "content_text", "runs", default=[])
            content_text = "".join(run.get("text", "") for run in content_runs)

            # Formatear datos finales
            return {
                "postId": post_data["post_id"],
                "channelID": post_data["channel_id"],
                "authorName": author_name,
                "thumbnail": thumbnails,
                "contentText": content_text,
                "likes": post_stats["likes"],
                "comments": post_stats["comments"]
            }

        # Ejecutar la función para cada post de manera concurrente
        tasks = [process_post(post) for post in community_tab.posts]
        posts = await asyncio.gather(*tasks)

        return posts

    except SystemExit:
        raise HTTPException(status_code=400, detail=f"No se pudo obtener datos del canal: {channel_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/post/{post_id}", tags=["Posts"])
def get_post(post_id: str):
    try:
        post = Post.from_post_id(post_id)
        return post.as_json()

    except SystemExit:
        raise HTTPException(status_code=400, detail=f"No se pudo obtener el post: {post_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/posts/{post_id}/stats", tags=["Posts"])
def get_post_stats(post_id: str):
    try:
        post = Post.from_post_id(post_id)
        post_data = post.as_json()

        # Convertir el texto de likes a número
        likes_text = post_data.get("vote_count", {}).get("simpleText", "0")
        likes = parse_count_text(likes_text)

        # Procesar comentarios
        post_data_comments = post.load_comments()
        comments = 0

        runs = safely_get_value_from_key(post_data_comments, "onResponseReceivedEndpoints", 0,
                                         "reloadContinuationItemsCommand", "continuationItems", 0,
                                         "commentsHeaderRenderer", "countText", "runs", default=[])

        if runs:
            comments_text = runs[0].get("text", "0")
            comments = parse_count_text(comments_text)

        return {
            "post_id": post_id,
            "likes": likes,
            "comments": comments
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Error al convertir valores: {str(e)}")
    except SystemExit:
        raise HTTPException(status_code=400, detail=f"No se pudo obtener estadísticas del post: {post_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/posts/{post_id}/comments", tags=["Comments"])
def create_comment(post_id: str, comment: str):
    try:
        post = Post.from_post_id(post_id)
        post.create_comment(comment)
        return {"message": "Comentario creado exitosamente"}

    except SystemExit:
        raise HTTPException(status_code=400, detail=f"No se pudo crear el comentario en el post: {post_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/posts/{post_id}/comments", tags=["Comments"])
def get_comments(post_id: str):
    try:
        post = Post.from_post_id(post_id)
        post.load_comments()
        comments = [comment.as_json() for comment in getattr(post, "comments", [])]

        if not comments:
            raise HTTPException(status_code=404, detail=f"No se encontraron comentarios para el post: {post_id}")

        return comments

    except SystemExit:
        raise HTTPException(status_code=400, detail=f"No se pudieron obtener comentarios del post: {post_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- RUTAS DE COMUNIDAD ---
@app.get("/community/{channel_name}/info", tags=["Community"])
def get_community_info(channel_name: str):
    try:
        community_tab = CommunityTab(channel_name)
        community_tab.load_posts()

        return {
            "channel_id": community_tab.channel_id,
            "posts_count": len(community_tab.posts),
            "visitor_data": community_tab.visitor_data,
        }

    except SystemExit:
        raise HTTPException(status_code=400, detail=f"No se pudo obtener la información del canal: {channel_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/community/{channel_name}/posts", tags=["Community"])
def get_paginated_posts(channel_name: str, page: int = 1, per_page: int = 10):
    try:
        community_tab = CommunityTab(channel_name)
        community_tab.load_posts()

        start = (page - 1) * per_page
        end = start + per_page

        return [post.as_json() for post in community_tab.posts[start:end]]

    except SystemExit:
        raise HTTPException(status_code=400, detail=f"No se pudieron obtener publicaciones del canal: {channel_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

